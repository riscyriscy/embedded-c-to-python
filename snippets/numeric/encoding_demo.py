"""Default text encoding on a station.

Run: LC_ALL=C PYTHONCOERCECLOCALE=0 python3 -X utf8=0 encoding_demo.py
"""

import csv
import locale
import sys
import tempfile
import textwrap
from collections.abc import Callable
from pathlib import Path

# A UART capture: a UTF-8 degree sign, then two bytes of line noise.
LOG = b"T=25.1\xc2\xb0C \xff\xfe\r\n"
EXCEL_CSV = (
    b"\xef\xbb\xbftime,volts\r\n1,3.3\r\n"  # "UTF-8 with BOM", as Excel saves it
)


def show(label: str, read: Callable[[], object]) -> None:
    try:
        result = ascii(read())  # ascii(): stdout itself is ASCII-only in this locale
    except (UnicodeDecodeError, KeyError) as exc:
        result = f"{type(exc).__name__}: {exc}"
    print(textwrap.fill(f"{label}: {result}", width=86, subsequent_indent="    "))


def round_trip(path: Path) -> bool:
    text = path.read_bytes().decode("utf-8", "surrogateescape")
    return text.encode("utf-8", "surrogateescape") == path.read_bytes()


def header_row(path: Path, encoding: str) -> list[str]:
    with path.open(newline="", encoding=encoding) as f:
        return list(csv.DictReader(f).fieldnames or [])


def first_time(path: Path, encoding: str) -> str:
    with path.open(newline="", encoding=encoding) as f:
        return next(csv.DictReader(f))["time"]


print("locale encoding:", locale.getencoding(), "| utf8_mode:", sys.flags.utf8_mode)
with tempfile.TemporaryDirectory() as tmp:
    log, table = Path(tmp) / "uart.log", Path(tmp) / "volts.csv"
    log.write_bytes(LOG)
    table.write_bytes(EXCEL_CSV)
    show("open(path), no encoding", log.read_text)
    show('encoding="utf-8"', lambda: log.read_text(encoding="utf-8"))
    show('utf-8, errors="replace"', lambda: log.read_text("utf-8", "replace"))
    show(
        'utf-8, errors="backslashreplace"',
        lambda: log.read_text("utf-8", "backslashreplace"),
    )
    show(
        'utf-8, errors="surrogateescape"',
        lambda: log.read_text("utf-8", "surrogateescape"),
    )
    show('encoding="cp1252" (Windows)', lambda: log.read_text("cp1252"))
    show("surrogateescape round trip", lambda: round_trip(log))
    show("csv header, utf-8", lambda: header_row(table, "utf-8"))
    show("csv header, utf-8-sig", lambda: header_row(table, "utf-8-sig"))
    show('row["time"], utf-8', lambda: first_time(table, "utf-8"))
    show('row["time"], utf-8-sig', lambda: first_time(table, "utf-8-sig"))
