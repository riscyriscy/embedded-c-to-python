"""struct format characters: sizes, alignment, byte order.

Run: python3 struct_sizes.py
"""

import ctypes
import struct

# Format character, C type on this machine, and what it holds.
CHARS = [
    ("x", "pad byte", "no value"),
    ("?", "_Bool", "bool"),
    ("b", "signed char / int8_t", "int"),
    ("B", "unsigned char / uint8_t", "int"),
    ("h", "short / int16_t", "int"),
    ("H", "unsigned short / uint16_t", "int"),
    ("i", "int / int32_t", "int"),
    ("I", "unsigned int / uint32_t", "int"),
    ("l", "long", "int"),
    ("L", "unsigned long", "int"),
    ("q", "long long / int64_t", "int"),
    ("Q", "unsigned long long / uint64_t", "int"),
    ("e", "(IEEE half, no C type)", "float"),
    ("f", "float", "float"),
    ("d", "double", "float"),
    ("s", "char[n]", "bytes"),
    ("p", "Pascal string char[n]", "bytes"),
]
print("char  native  '<'  native align  C type                        Python value")
for char, ctype, pytype in CHARS:
    native = struct.calcsize("@" + char)
    standard = struct.calcsize("<" + char)
    align = struct.calcsize("@B" + char) - native  # padding after one byte, plus size
    print(f"{char:>4}  {native:>6}  {standard:>3}  {align:>12}  {ctype:<28} {pytype}")

print()
print("prefix  byte order        size and alignment    L  H=0x1234")
PREFIXES = [
    ("@", "native"),
    ("=", "native"),
    ("<", "little-endian"),
    (">", "big-endian"),
    ("!", "big (network)"),
]
for prefix, order in PREFIXES:
    sizes = "native, aligned" if prefix == "@" else "standard, packed"
    print(
        f"{prefix:>4}    {order:<17} {sizes:<20} {struct.calcsize(prefix + 'L'):>2}"
        f"  {struct.pack(prefix + 'H', 0x1234).hex(' ')}"
    )


class U8U32(ctypes.Structure):
    _fields_ = [("a", ctypes.c_uint8), ("b", ctypes.c_uint32)]


class U32U8(ctypes.Structure):
    _fields_ = [("a", ctypes.c_uint32), ("b", ctypes.c_uint8)]


class U8U32U8(ctypes.Structure):
    _fields_ = [("a", ctypes.c_uint8), ("b", ctypes.c_uint32), ("c", ctypes.c_uint8)]


# ctypes.Structure follows the C layout rules. '@' pads between fields like C, but
# adds no tail padding unless the format ends in a zero-count field such as 0I.
print()
print("layout        ctypes  '@'  '@' + 0I  '<'")
LAYOUTS = [
    ("u8, u32", U8U32, "BI"),
    ("u32, u8", U32U8, "IB"),
    ("u8, u32, u8", U8U32U8, "BIB"),
]
for name, cls, fmt in LAYOUTS:
    print(
        f"{name:<13} {ctypes.sizeof(cls):>6}  {struct.calcsize('@' + fmt):>3}"
        f"  {struct.calcsize('@' + fmt + '0I'):>8}  {struct.calcsize('<' + fmt):>2}"
    )
