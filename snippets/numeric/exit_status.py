"""Exit status for each way a Python process can end. Run: python3 exit_status.py"""

import os
import signal
import subprocess
import sys

PRELUDE = "import os, sys, threading, time; "
# (code, signal to send once the child has printed "ready")
CASES: list[tuple[str, int | None]] = [
    ("pass", None),
    ("raise ValueError('boom')", None),
    ("raise SystemExit('bad config')", None),
    ("raise SystemExit", None),
    ("sys.exit(3)", None),
    ("sys.exit(256)", None),
    ("sys.exit(-1)", None),
    ("os._exit(7)", None),
    ("print('data', end=''); os._exit(0)", None),
    ("threading.Thread(target=lambda: 1 / 0).start()", None),
    ("print('ready', flush=True); time.sleep(30)", signal.SIGINT),
    ("print('ready', flush=True); time.sleep(30)", signal.SIGTERM),
]
ENV = {k: v for k, v in os.environ.items() if k != "PYTHONUNBUFFERED"}

print(f"{'code':<48} {'status':>6} {'shell':>5}  {'stdout':<7} stderr")
for code, sig in CASES:
    child = subprocess.Popen(
        [sys.executable, "-c", PRELUDE + code],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=ENV,
    )
    if sig is not None:
        assert child.stdout is not None
        child.stdout.readline()  # wait for "ready": the interpreter is up
        child.send_signal(sig)
    out, err = child.communicate()
    status = child.returncode
    shell = status if status >= 0 else 128 - status  # how a shell reports a signal
    last = (err.strip().splitlines()[-1:] or [""])[0].partition(":")[0]
    shown = code if sig is None else f"time.sleep(30), then {signal.Signals(sig).name}"
    print(f"{shown:<48} {status:>6} {shell:>5}  {out.strip()!r:<7} {last}")
