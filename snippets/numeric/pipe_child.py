"""Child process for pipe_parent.py: three lines, half a second apart."""

import io
import sys
import time

if "--line-buffered" in sys.argv:
    assert isinstance(sys.stdout, io.TextIOWrapper)
    sys.stdout.reconfigure(line_buffering=True)
for n in range(1, 4):
    if n > 1:
        time.sleep(0.5)
    print(f"sample {n}", flush="--flush" in sys.argv)
