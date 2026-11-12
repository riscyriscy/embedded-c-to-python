"""Report the running Python and whether it is in a virtual environment. Run: python3 venv_info.py"""

import sys
from importlib.metadata import distributions

in_venv = (
    sys.prefix != sys.base_prefix
)  # a venv points sys.prefix at itself and keeps the real install in base_prefix
print(f"in a virtual environment: {in_venv}")
print(f"interpreter:     {sys.executable}")
print(f"sys.prefix:      {sys.prefix}")
print(f"sys.base_prefix: {sys.base_prefix}")
names = sorted({d.metadata["Name"] for d in distributions()}, key=str.lower)
print(f"{len(names)} installed distributions: {', '.join(names) or 'none'}")
