"""Does `finally` run when the process is stopped by a signal? Run: python shutdown_signals.py

The parent starts a child that holds a bench supply on and waits. The parent sends SIGINT,
SIGTERM or SIGKILL and reports the exit status and whether the child's `finally` ran.
Mode "term-handler" installs the idiom that turns SIGTERM into SystemExit. POSIX only.
"""

import signal
import subprocess
import sys
import time


def child(mode: str) -> None:
    if mode == "term-handler":
        signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(128 + signum))
    try:
        print("OUTP ON", flush=True)
        time.sleep(30)  # the test runs here
    finally:
        print("OUTP OFF", flush=True)


def run(mode: str, sig: signal.Signals) -> None:
    proc = subprocess.Popen(
        [sys.executable, __file__, "child", mode], stdout=subprocess.PIPE, text=True
    )
    assert proc.stdout is not None
    assert proc.stdout.readline().strip() == "OUTP ON"
    proc.send_signal(sig)
    rest = proc.stdout.read()
    status = proc.wait()
    print(
        f"{mode:12s} {sig.name:8s} exit status {status:4d}  finally ran: {'OUTP OFF' in rest}"
    )


if __name__ == "__main__":
    if sys.argv[1:2] == ["child"]:
        child(sys.argv[2])
    else:
        run("plain", signal.SIGINT)
        run("plain", signal.SIGTERM)
        run("term-handler", signal.SIGTERM)
        run("term-handler", signal.SIGKILL)
