"""struct beyond pack and unpack: offsets, arrays, floats, 24-bit fields.

Run: python3 struct_tricks.py
"""

import struct

# ---- pack_into and unpack_from work at an offset in an existing buffer ----
frame = bytearray(12)
struct.pack_into("<BHI", frame, 2, 0xA5, 0x1234, 0xDEADBEEF)
print("pack_into  :", frame.hex(" "))
print("unpack_from:", struct.unpack_from("<BHI", frame, 2))

# ---- iter_unpack walks an array of records; the size must divide evenly ----
log = bytes.fromhex("0a00 f401 1400 0cfe")  # two records of (uint16, int16)
print("iter_unpack:", list(struct.iter_unpack("<Hh", log)))
try:
    list(struct.iter_unpack("<Hh", log + b"\x00"))
except struct.error as exc:
    print("odd length :", exc)

# ---- s is fixed-length text padded with NUL; p stores a length byte first ----
print(
    "4s:",
    struct.pack("<4s", b"ab").hex(" "),
    "| 5p:",
    struct.pack("<5p", b"abc").hex(" "),
)
print(
    "unpack 4s:",
    struct.unpack("<4s", b"ab\x00\x00"),
    "| 5p:",
    struct.unpack("<5p", bytes.fromhex("0361626300")),
)

# ---- there are no bit fields: unpack the word, then shift and mask ----
(ctrl,) = struct.unpack("<H", bytes.fromhex("b704"))
mode, gain, enable = (ctrl >> 4) & 0x7, (ctrl >> 8) & 0xF, ctrl & 1
print(f"ctrl 0x{ctrl:04x}: mode {mode}, gain {gain}, enable {enable}")

# ---- f and e decode IEEE 754 binary32 and binary16; d is binary64 ----
print("f:", struct.unpack("<f", bytes.fromhex("0000803f")), "1.0 from firmware")
for code in "fed":
    packed = struct.pack("<" + code, 3.3)
    print(f"3.3 as '<{code}': {packed.hex(' '):<23}", struct.unpack("<" + code, packed))

# ---- struct raises where a C cast truncates ----
for fmt, value in [("<B", 256), ("<h", 40000), ("<f", 1e39)]:
    try:
        struct.pack(fmt, value)
    except (struct.error, OverflowError) as exc:
        name = "struct.error" if isinstance(exc, struct.error) else "OverflowError"
        print(f"pack({fmt!r}, {value}): {name}: {exc}")

# ---- 24-bit fields: slice three bytes, let int.from_bytes do the sign ----
status, raw, crc = struct.unpack("<B3sH", bytes.fromhex("01 feffff 3412"))
print(
    "24-bit:",
    int.from_bytes(raw, "little", signed=True),
    "| status",
    status,
    "| crc",
    hex(crc),
)
print(
    "24-bit:",
    int.from_bytes(b"\x80\x00\x00", "big", signed=True),
    (-2).to_bytes(3, "big", signed=True).hex(),
)
