"""Strings and formatting for a C programmer. Run: python3 text_strings.py"""

# ---- str is immutable Unicode text; bytes is a separate type ----
name = "µC-rev2"
print(
    f"characters={len(name)}, utf-8 bytes={len(name.encode())}, "
    f"latin-1 bytes={len(name.encode('latin-1'))}"
)
try:
    name[0] = "u"  # type: ignore[index]
except TypeError as exc:
    print(f"TypeError: {exc}")

# ---- slicing, searching, splitting ----
line = "  uart0 : 115200 baud, 8N1  "
text = line.strip()
print(repr(text), text[:5], text[-3:], text[::-1][:4])
print("find:", text.find("x"), "| startswith:", text.startswith(("uart", "spi")))
try:
    text.index("x")  # like find, but raises instead of returning -1
except ValueError as exc:
    print(f"index: ValueError: {exc}")
print("removeprefix:", "0xBEEF".removeprefix("0x"), "| casefold:", "ABC".casefold() == "abc")

# ---- parse KEY=VALUE lines with partition ----
CONFIG = """
# serial settings
port = /dev/ttyUSB0
baud = 115200
timeout=0.5
bad line without equals
flags = 0x1F
"""
settings: dict[str, str] = {}
for number, raw in enumerate(CONFIG.splitlines(), start=1):
    entry = raw.strip()
    if not entry or entry.startswith("#"):
        continue
    key, sep, value = entry.partition("=")
    if not sep:
        print(f"line {number}: no '=' in {entry!r}")
        continue
    settings[key.strip()] = value.strip()
print(settings)
print(int(settings["baud"]), float(settings["timeout"]), int(settings["flags"], 0))  # base 0: 0x ok

# ---- format specifications ----
word = 0xBEEF
print(f"{word:#06x} {word:#x} {word:016b} [{word:>8d}] [{word:<8d}] [{word:^8d}]")
print(f"{3.14159:8.3f}|{1234567:,}|{0.256:.1%}|{'abc':^9}|{'abc':*<6}|{word=}")
print(f"{name!r} {name!s} {1e-9:.2e} {255:02X}")

# ---- join, bytes and hex ----
parts = ["A5", "10", "04", "00"]
joined = " ".join(parts)
frame = bytes.fromhex(joined)
print(joined, "->", frame, "->", frame.hex(" "), list(frame))
print(frame.decode("latin-1").encode("latin-1") == frame)  # every byte maps to one character
hexpart = " ".join(f"{b:02x}" for b in b"Hello\x00\xff!")
ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in b"Hello\x00\xff!")
print(f"{hexpart}  |{ascii_part}|")  # one row of a hexdump
