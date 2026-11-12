"""Three Linux real-time hints: CPU affinity, locked memory and allocation tracking.

Run: python3 rt_hints.py        (Linux only; mlockall needs root or a large RLIMIT_MEMLOCK)
"""

from __future__ import annotations

import ctypes
import mmap
import os
import resource
import time
import tracemalloc

MCL_CURRENT, MCL_FUTURE = 1, 2  # <sys/mman.h> on Linux, x86-64 and aarch64


def locked_kib() -> int:
    """Memory that the kernel keeps in RAM for this process, from /proc/self/status."""
    for line in open("/proc/self/status"):
        if line.startswith("VmLck:"):
            return int(line.split()[1])
    return -1


def minor_faults() -> int:
    return resource.getrusage(resource.RUSAGE_SELF).ru_minflt


def touch(buf: mmap.mmap) -> None:
    for i in range(0, len(buf), mmap.PAGESIZE):
        buf[i] = 1


def affinity_demo() -> None:
    print("1. CPU affinity")
    print("   allowed CPUs at start :", sorted(os.sched_getaffinity(0)))
    os.sched_setaffinity(0, {1})
    print("   after setaffinity({1}):", sorted(os.sched_getaffinity(0)))
    t = threading_cpu()
    print("   a new thread inherits :", t)
    os.sched_setaffinity(0, set(range(os.cpu_count() or 1)))


def threading_cpu() -> list[int]:
    import threading

    out: list[int] = []
    th = threading.Thread(target=lambda: out.extend(sorted(os.sched_getaffinity(0))))
    th.start()
    th.join()
    return out


def memory_demo() -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    soft, hard = resource.getrlimit(resource.RLIMIT_MEMLOCK)
    print("2. Locked memory")
    print(f"   RLIMIT_MEMLOCK soft/hard: {soft} / {hard}")
    for label, lock in (("without mlockall", False), ("with mlockall", True)):
        if lock and libc.mlockall(MCL_CURRENT | MCL_FUTURE) != 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        f0 = minor_faults()
        buf = mmap.mmap(-1, 64 * 1024 * 1024)  # anonymous pages, supplied lazily by the kernel
        f1 = minor_faults()
        t0 = time.perf_counter()
        touch(buf)
        t1 = time.perf_counter()
        f2 = minor_faults()
        touch(buf)
        f3 = minor_faults()
        ms = (t1 - t0) * 1000
        print(f"   {label:<17} faults: map {f1 - f0:>5}, first touch {f2 - f1:>5} ({ms:3.0f} ms), "
              f"second touch {f3 - f2:>2}   VmLck {locked_kib() // 1024:>4} MiB")
        buf.close()
    libc.munlockall()
    pid = os.fork()
    if pid == 0:  # child: the same call without privilege
        os.setuid(65534)
        rc = libc.mlockall(MCL_CURRENT | MCL_FUTURE)
        print(f"   as uid 65534      mlockall returned {rc}, errno {ctypes.get_errno()} "
              f"({os.strerror(ctypes.get_errno())})")
        os._exit(0)
    os.waitpid(pid, 0)


def build() -> list[bytes]:
    kept = []
    for _ in range(200_000):
        kept.append(bytes(1000))  # the "leak": every frame buffer is kept
    return kept


def best_ms(repeats: int = 5) -> float:
    best = float("inf")
    for _ in range(repeats):
        t0 = time.perf_counter()
        build()
        best = min(best, time.perf_counter() - t0)
    return best * 1000


def tracemalloc_demo() -> None:
    print("3. tracemalloc")
    plain = best_ms()
    tracemalloc.start(1)  # keep 1 frame of traceback per allocation
    traced = best_ms()
    tracemalloc.clear_traces()
    snap0 = tracemalloc.take_snapshot()
    kept = build()
    snap1 = tracemalloc.take_snapshot()
    cur, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"   200000 x 1000 bytes, best of 5: {plain:.0f} ms plain, {traced:.0f} ms traced")
    mib = 2**20
    print(f"   traced memory {cur / mib:.1f} MiB, peak {peak / mib:.1f} MiB, {len(kept)} buffers kept")
    top = snap1.compare_to(snap0, "lineno")[0]
    frame = top.traceback[0]
    print(f"   top growth: {os.path.basename(frame.filename)}:{frame.lineno} "
          f"size=+{top.size_diff / 2**20:.0f} MiB count=+{top.count_diff}")


if __name__ == "__main__":
    affinity_demo()
    memory_demo()
    tracemalloc_demo()
