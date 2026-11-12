"""A rig tool that hangs: the main thread waits for a reply that never comes.

Run: python3 hang_demo.py [--watchdog | --signal | --poll]
"""

import faulthandler
import queue
import signal
import sys
import threading
import time

replies: queue.Queue[str] = queue.Queue()


def reader() -> None:
    while True:
        time.sleep(0.5)  # stands in for a serial read that finds no data


def wait_for_reply(timeout: float | None = None) -> str:
    return replies.get(timeout=timeout)  # timeout=None blocks for ever


def poll_for_reply() -> str:
    while True:  # a retry loop: wakes up every 0.2 s, so the interpreter keeps running Python code
        try:
            return replies.get(timeout=0.2)
        except queue.Empty:
            continue


def main() -> None:
    if "--watchdog" in sys.argv:
        faulthandler.dump_traceback_later(2, exit=True)  # after 2 s: print every stack, then exit
    if "--signal" in sys.argv:
        faulthandler.register(signal.SIGUSR1)  # kill -USR1 PID prints every stack
    threading.Thread(target=reader, name="uart-reader", daemon=True).start()
    print("waiting for the device", flush=True)
    if "--poll" in sys.argv:
        poll_for_reply()
    else:
        wait_for_reply()


if __name__ == "__main__":
    main()
