"""psutil: watch the host and a child process, and stop a process tree.

Typical uses in a test rig: check free disk before a capture, detect a memory leak in a
tool under test, make sure no helper process is left running after a test.
Numbers depend on the machine, so the script prints yes/no checks. Run: python3 host_monitor.py
"""

import contextlib
import subprocess
import sys
import time
from dataclasses import dataclass

import psutil

# The child allocates 40 MB, burns CPU for about 1.5 s and starts a grandchild that sleeps.
CHILD_CODE = """
import subprocess, sys, time
grandchild = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
block = bytearray(40 * 1024 * 1024)
block[::4096] = b"x" * len(block[::4096])  # touch the pages so they count as resident memory
end = time.monotonic() + 1.5
while time.monotonic() < end:
    sum(range(10_000))
time.sleep(60)
"""


@dataclass(frozen=True)
class Sample:
    t_s: float
    cpu_percent: float  # of one core: 100 means one core fully busy
    rss_mb: float  # resident memory (RAM actually used)
    threads: int


def sample(proc: psutil.Process, t0: float) -> Sample:
    # cpu_percent(interval=None) compares with the previous call, so the first value is 0.0
    return Sample(
        time.monotonic() - t0,
        proc.cpu_percent(None),
        proc.memory_info().rss / 2**20,
        proc.num_threads(),
    )


def kill_tree(proc: psutil.Process, timeout_s: float = 3.0) -> dict[int, int | None]:
    """Terminate a process and all of its descendants. Returns {pid: exit status} for each.

    wait_procs collects the exit status of a child of this process (-15 after SIGTERM) and
    reports None for any other process, such as a grandchild.
    """
    victims = [*proc.children(recursive=True), proc]
    for p in victims:
        with contextlib.suppress(psutil.NoSuchProcess):  # already gone
            p.terminate()
    gone, alive = psutil.wait_procs(victims, timeout=timeout_s)
    for p in alive:  # did not exit on SIGTERM: force it
        p.kill()
    gone += psutil.wait_procs(alive, timeout=timeout_s)[0]
    return {p.pid: getattr(p, "returncode", None) for p in gone}


def main() -> None:
    # 1. Host facts: preflight checks before a capture or a long test
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    print(
        "cpus:",
        (psutil.cpu_count(logical=True) or 0) >= 1,
        "| ram:",
        mem.total > 2**28,
        0 <= mem.percent <= 100,
    )
    print(
        "disk free > 0:",
        disk.free > 0,
        "| boot time in the past:",
        psutil.boot_time() < time.time(),
    )
    print(
        "python in process list:",
        any("python" in (p.info["name"] or "") for p in psutil.process_iter(["name"])),
    )

    # 2. Watch a child process: CPU, memory and threads over time
    child = subprocess.Popen([sys.executable, "-c", CHILD_CODE])
    proc = psutil.Process(child.pid)
    t0 = time.monotonic()
    proc.cpu_percent(None)  # prime the counter
    time.sleep(0.2)
    samples = []
    for _ in range(5):
        time.sleep(0.3)
        samples.append(sample(proc, t0))
    running = proc.status() in (psutil.STATUS_RUNNING, psutil.STATUS_SLEEPING)
    print(
        "child alive:",
        running,
        "| command line starts with python:",
        proc.cmdline()[0] == sys.executable,
    )
    print("resident memory above 40 MB:", max(s.rss_mb for s in samples) > 40)
    print("cpu was busy while the loop ran:", max(s.cpu_percent for s in samples) > 50)
    print("has a grandchild:", len(proc.children(recursive=True)) == 1)

    # 3. Leave nothing behind: stop the whole tree and check that it is gone
    statuses = kill_tree(proc)
    after = child.wait()  # no zombie remains, but wait_procs already took the status: 0 here
    print(
        "stopped:",
        len(statuses),
        "| child exit status:",
        statuses[child.pid],
        "| Popen.wait() afterwards:",
        after,
        "| still running:",
        proc.is_running(),
    )
    try:
        proc.memory_info()
    except psutil.NoSuchProcess as exc:
        print("NoSuchProcess:", type(exc).__name__)


if __name__ == "__main__":
    main()
