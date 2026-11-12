"""A local file named like a library hides the library. Run: python3 shadow_demo.py"""

import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

TOOL = """\
import os
import struct

local = os.path.realpath(struct.__file__) == os.path.realpath("struct.py")
print("struct is", "the local struct.py" if local else "the standard library")
struct.pack("<H", 1)
"""
FILES = {
    "struct.py": '"""My frame helpers."""\n',
    "tool.py": TOOL,
    "serial.py": "import serial\n\nport = serial.Serial('/dev/ttyUSB0')\n",
}
CASES = [
    ("python tool.py", ["tool.py"]),
    ("python -c 'import pickle'", ["-c", "import pickle"]),
    ("python -I tool.py", ["-I", "tool.py"]),
    ("python serial.py", ["serial.py"]),
]


def run(folder: Path, args: list[str]) -> list[str]:
    """Run python in folder; return the stdout lines and the last stderr line."""
    done = subprocess.run(
        [sys.executable, *args], cwd=folder, capture_output=True, text=True, check=False
    )
    lines = done.stdout.splitlines() + done.stderr.strip().splitlines()[-1:]
    return [line.replace(str(folder), "DIR") for line in lines]


with tempfile.TemporaryDirectory() as tmp:
    folder = Path(tmp)
    for name, text in FILES.items():
        (folder / name).write_text(text, encoding="utf-8")
    for label, args in CASES:
        print(f"$ {label}")
        for line in run(folder, args):
            print(
                textwrap.fill(line, 86, initial_indent="  ", subsequent_indent="    ")
            )
