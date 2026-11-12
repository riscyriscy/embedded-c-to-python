"""C habit versus Python idiom: error codes versus exceptions. Run: python3 idiom_errors.py"""

import struct
import tempfile
from pathlib import Path

MAGIC = 0xCA
OK, ERR_OPEN, ERR_SHORT, ERR_MAGIC, ERR_SUM = 0, -1, -2, -3, -4
STATUS_NAMES = {
    OK: "OK",
    ERR_OPEN: "ERR_OPEN",
    ERR_SHORT: "ERR_SHORT",
    ERR_MAGIC: "ERR_MAGIC",
    ERR_SUM: "ERR_SUM",
}


def load_c_style(path: Path, out: list[int]) -> int:
    """Return a status code, fill the caller's list, release the file on every path."""
    try:
        f = open(path, "rb")  # C shape: open, check, and close by hand at the end
    except OSError:
        return ERR_OPEN
    status = OK
    data = f.read()
    if len(data) < 3:
        status = ERR_SHORT
    elif data[0] != MAGIC:
        status = ERR_MAGIC
    elif len(data) != 3 + 2 * data[1]:
        status = ERR_SHORT
    else:
        total = 0
        for i in range(len(data) - 1):
            total = (total + data[i]) & 0xFF
        if total != data[-1]:
            status = ERR_SUM
        else:
            for i in range(data[1]):
                out.append(int.from_bytes(data[2 + 2 * i : 4 + 2 * i], "little", signed=True))
    f.close()
    return status


class CalibrationError(Exception):
    """The file was read but its contents are not a valid calibration blob."""


def load_pythonic(path: Path) -> list[int]:
    data = path.read_bytes()  # a missing file raises FileNotFoundError, which names the path
    if len(data) < 3:
        raise CalibrationError(f"{len(data)} bytes, need at least 3")
    if data[0] != MAGIC:
        raise CalibrationError(f"magic {data[0]:#04x}, expected {MAGIC:#04x}")
    count = data[1]
    if len(data) != 3 + 2 * count:
        raise CalibrationError(f"{len(data)} bytes for {count} values, expected {3 + 2 * count}")
    if sum(data[:-1]) & 0xFF != data[-1]:
        raise CalibrationError("checksum mismatch")
    return list(struct.unpack_from(f"<{count}h", data, 2))


def make_blob(values: list[int]) -> bytes:
    body = bytes([MAGIC, len(values)]) + struct.pack(f"<{len(values)}h", *values)
    return body + bytes([sum(body) & 0xFF])


good = make_blob([100, -250, 3000])
with tempfile.TemporaryDirectory() as tmp:
    cases = {
        "good": good,
        "bad magic": b"\x00" + good[1:],
        "truncated": good[:-3],
        "bad checksum": good[:-1] + b"\x00",
        "empty": b"",
    }
    paths = {}
    for name, blob in cases.items():
        paths[name] = Path(tmp) / f"{name.replace(' ', '_')}.cal"
        paths[name].write_bytes(blob)
    paths["missing file"] = Path(tmp) / "nothing_here.cal"

    for name, path in paths.items():
        values: list[int] = []
        rc = load_c_style(path, values)
        try:
            result = f"values {load_pythonic(path)}"
        except (OSError, CalibrationError) as exc:
            result = f"{type(exc).__name__}: {str(exc).replace(tmp, '<tmp>')}"
        print(f"{name:13} C style {STATUS_NAMES[rc]:9} | Pythonic {result}")
