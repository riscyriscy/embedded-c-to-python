"""Numeric traps a C programmer meets in Python. Run: python3 numeric_traps.py"""

import ctypes
import math
import tempfile
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path


def show(label: str, *values: object) -> None:
    print(f"  {label:<24}", *values)


def wrap(value: int, bits: int, signed: bool) -> int:
    """The C cast to a fixed-width integer type, written with a mask."""
    value &= (1 << bits) - 1
    if signed and value >> (bits - 1):  # sign bit set: subtract 2**bits
        value -= 1 << bits
    return value


# ---- (a) casts: ctypes gives the exact C result, the mask idiom needs a sign step ----
print("(a) casts: ctypes, mask only, mask plus sign step")
CASTS = [
    ("(uint16_t)0x10000", ctypes.c_uint16, 0x10000),
    ("(int16_t)0xFFFF", ctypes.c_int16, 0xFFFF),
    ("(int16_t)40000", ctypes.c_int16, 40000),
    ("(uint32_t)-1", ctypes.c_uint32, -1),
    ("(int8_t)200", ctypes.c_int8, 200),
]
for label, ctype, value in CASTS:
    bits = ctypes.sizeof(ctype) * 8
    masked = value & ((1 << bits) - 1)
    wrapped = wrap(value, bits, signed=ctype(-1).value < 0)
    show(label, f"{ctype(value).value:>11} {masked:>11} {wrapped:>11}")

# ---- (b) round() is round-half-to-even; C round() and lround() go away from zero ----
print("(b) rounding")
show("round(0.5 .. 3.5):", [round(x + 0.5) for x in range(4)])


def round_half_away(x: float) -> int:
    """C lround(): ties go away from zero. Decimal(x) is the exact binary value."""
    return int(Decimal(x).quantize(Decimal(1), rounding=ROUND_HALF_UP))


neg = [-0.5, -1.5, -2.5]
show("round():", [round(x) for x in neg])
show("floor(x + 0.5):", [math.floor(x + 0.5) for x in neg])
show("round_half_away():", [round_half_away(x) for x in neg])
tiny = 0.49999999999999994  # the largest double below 0.5
show("just below 0.5:", round(tiny), math.floor(tiny + 0.5), round_half_away(tiny))
codes = range(4096)  # 12-bit ADC, 2.5 V reference: mV = code * 2500 / 4096
by_round = [round(c * 2500 / 4096) for c in codes]
# Integer add-half, as firmware does it: floor division of a non-negative value.
by_int = [(c * 2500 + 2048) // 4096 for c in codes]
by_lround = [round_half_away(c * 2500 / 4096) for c in codes]
show("ADC round() differs:", [c for c in codes if by_round[c] != by_int[c]])
show("ADC add-half == lround:", by_int == by_lround)

# ---- (c) NaN passes comparisons that are written as "bad if outside" ----
print("(c) NaN")
LO, HI = -40.0, 125.0


def classify(c: float) -> str:
    return "out of range" if c < LO or c > HI else "ok"


def classify_safe(c: float) -> str:
    return "ok" if LO <= c <= HI else "out of range"  # NaN fails every comparison


nan = float("nan")
show("classify(nan):", classify(nan))
show("classify_safe(nan):", classify_safe(nan))
show("max(1.0, nan):", max(1.0, nan), "| max(nan, 1.0):", max(nan, 1.0))
for xs in ([3.0, 1.0, 2.0, nan], [3.0, nan, 1.0, 2.0], [nan, 3.0, 1.0, 2.0]):
    show(f"sorted({xs}):", sorted(xs))
show("0.1 + 0.2 == 0.3:", 0.1 + 0.2 == 0.3, "| isclose:", math.isclose(0.1 + 0.2, 0.3))
show("isclose(1e-12, 0.0):", math.isclose(1e-12, 0.0))
show("... with abs_tol=1e-9:", math.isclose(1e-12, 0.0, abs_tol=1e-9))

# ---- (d) int(s, 0) is not strtol(s, 0) ----
print("(d) int(s, 0) versus strtol(s, 0)")
libc = ctypes.CDLL(None)  # Linux and macOS: the C library that Python itself uses
libc.strtol.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_char_p), ctypes.c_int]
libc.strtol.restype = ctypes.c_long


def strtol(text: str) -> str:
    buf = ctypes.create_string_buffer(text.encode())
    end = ctypes.c_char_p()
    value = libc.strtol(buf, ctypes.byref(end), 0)
    return f"{value} rest {end.value!r}"


def int0(text: str) -> str:
    try:
        return str(int(text, 0))
    except ValueError:
        return "ValueError"


for text in ["0x1F", "010", "08", "0_1", "1_000", "00", " 12 "]:
    show(repr(text), f"int: {int0(text):<11} strtol: {strtol(text)}")


def parse_int(text: str) -> int:
    """Base 0 only when a 0x, 0o or 0b prefix is present; otherwise ASCII decimal digits."""
    body = text.strip().lower().lstrip("+-")
    if body[:2] in ("0x", "0o", "0b"):
        return int(text, 0)
    # int(s, 10) alone also takes 1_000 and Arabic-Indic digits
    if not (body.isascii() and body.isdecimal()):
        raise ValueError(f"not a decimal integer: {text!r}")
    return int(text, 10)


def parse_int_or_error(text: str) -> str:
    try:
        return str(parse_int(text))
    except ValueError:
        return "ValueError"


show("int(t, 10):", [int(t, 10) for t in ["1_000", "\u0663", " 12 "]])
show("parse_int:", [parse_int(t) for t in ["03", "010", "0x1F", "-0b11"]])
show(
    "parse_int rejects:", [parse_int_or_error(t) for t in ["1_000", "\u0663", "\u00b2", "1e3", ""]]
)
show("float(v):", [float(v) for v in ["010", "nan", "inf"]])
show("isfinite(float(v)):", [math.isfinite(float(v)) for v in ["010", "nan", "inf"]])

# ---- (e) str.splitlines() splits on more than \n ----
print("(e) splitlines")
raw = b"ok\r\nA\x0cB\x1cC\xc2\x85D\xe2\x80\xa8E\nlast\n"  # noise: FF, FS, NEL, LS
show("str.splitlines:", raw.decode().splitlines())
show("bytes.splitlines:", raw.splitlines())
show("bytes.split:", [ln.rstrip(b"\r") for ln in raw.split(b"\n")])
with tempfile.TemporaryDirectory() as tmp:
    log = Path(tmp) / "uart.log"
    log.write_bytes(raw)
    with log.open(encoding="utf-8") as f:
        show("iterate a file:", [line.rstrip("\n") for line in f])
    # A lone CR ends a line for bytes.splitlines() and for a text file; only split(b"\n") keeps it.
    cr = b"a\rb\nc\n"
    show("CR, bytes.splitlines:", cr.splitlines())
    show("CR, bytes.split:", cr.split(b"\n"))
    log.write_bytes(cr)
    with log.open(encoding="utf-8") as f:
        show("CR, iterate a file:", [line.rstrip("\n") for line in f])
    # A byte that is not valid UTF-8 stops a strict decode; errors="replace" keeps the line.
    log.write_bytes(b"ok\xff\nnext\n")
    try:
        with log.open(encoding="utf-8") as f:
            show("0xFF, strict:", list(f))
    except UnicodeDecodeError as exc:
        show("0xFF, strict:", type(exc).__name__)
    with log.open(encoding="utf-8", errors="replace") as f:
        show("0xFF, replace:", ascii([line.rstrip("\n") for line in f]))
