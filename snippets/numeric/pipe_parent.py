"""Show when a child's print() output reaches a pipe. Run: python3 pipe_parent.py"""

import os
import subprocess
import sys
import time
from pathlib import Path

CHILD = str(Path(__file__).with_name("pipe_child.py"))
CASES: list[tuple[str, list[str], list[str], dict[str, str]]] = [
    ("print(...)", [], [], {}),
    ("print(..., flush=True)", [], ["--flush"], {}),
    ("reconfigure(line_buffering=True)", [], ["--line-buffered"], {}),
    ("python -u", ["-u"], [], {}),
    ("PYTHONUNBUFFERED=1", [], [], {"PYTHONUNBUFFERED": "1"}),
]
BASE = {k: v for k, v in os.environ.items() if k != "PYTHONUNBUFFERED"}

print(f"{'child writes with':<34} sample 1, 2, 3 arrive at (seconds)")
for label, flags, args, extra in CASES:
    start = time.monotonic()
    child = subprocess.Popen(
        [sys.executable, *flags, CHILD, *args],
        stdout=subprocess.PIPE,
        text=True,
        env=BASE | extra,
    )
    assert child.stdout is not None
    arrivals = []
    for _line in child.stdout:  # blocks until the child's buffer reaches the pipe
        seen = round((time.monotonic() - start) * 2) / 2  # nearest half second
        arrivals.append(f"{seen:.1f}")
    child.wait()
    print(f"{label:<34}", "  ".join(arrivals))
