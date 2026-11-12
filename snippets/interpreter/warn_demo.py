"""Two quiet problems that Python's development mode and -W error make visible.

Run from this folder: python3 warn_demo.py, python3 -X dev warn_demo.py, python3 -W error::DeprecationWarning warn_demo.py
"""

from pathlib import Path

from legacy_clock import stamp


def first_line(path: Path) -> str:
    return open(path).readline().rstrip()  # the file object is never closed


print(first_line(Path("../files/data/limits.toml")))
print(len(stamp()), "characters in the time stamp")
