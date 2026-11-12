"""Wake-up lateness of a SCHED_FIFO thread that sleeps 5 ms, next to a busy Python thread.

Linux only, run as root (or with CAP_SYS_NICE). The real-time thread sleeps 5 ms, 400 times,
and records how much longer than 5 ms each sleep took. Four cases: nothing else running, a busy thread in the
same process, the same with a shorter switch interval, and the loop in a second process.
"""

import multiprocessing
import os
import statistics
import sys
import threading
import time

PERIOD = 0.005
SAMPLES = 400


def lateness() -> list[float]:
    """Run as SCHED_FIFO priority 50 and return how late each wake-up was, in seconds."""
    os.sched_setscheduler(0, os.SCHED_FIFO, os.sched_param(50))
    late = []
    for _ in range(SAMPLES):
        start = time.monotonic()
        time.sleep(PERIOD)
        late.append(time.monotonic() - start - PERIOD)
    return late


def busy(stop: threading.Event) -> None:
    while not stop.is_set():
        pass


def in_thread() -> list[float]:
    result: list[float] = []
    worker = threading.Thread(target=lambda: result.extend(lateness()))
    worker.start()
    worker.join()
    return result


def in_process() -> list[float]:
    with multiprocessing.get_context("spawn").Pool(1) as pool:
        return pool.apply(lateness)


def report(name: str, late: list[float]) -> None:
    ms = sorted(x * 1000 for x in late)
    p99 = ms[int(0.99 * len(ms)) - 1]
    print(
        f"{name:<34} median {statistics.median(ms):5.2f}  p99 {p99:5.2f}  max {ms[-1]:5.2f}  ms"
    )


def main() -> None:
    gil = getattr(sys, "_is_gil_enabled", lambda: True)()
    print(
        sys.version.split()[0],
        "GIL" if gil else "no GIL",
        "switch interval",
        sys.getswitchinterval(),
        "s",
    )
    report("no other thread", in_thread())
    stop = threading.Event()
    threading.Thread(target=busy, args=(stop,), daemon=True).start()
    report("busy thread, same process", in_thread())
    sys.setswitchinterval(0.0005)
    report("busy thread, switch interval 0.5 ms", in_thread())
    sys.setswitchinterval(0.005)
    report("busy thread, loop in a 2nd process", in_process())
    stop.set()


if __name__ == "__main__":
    main()
