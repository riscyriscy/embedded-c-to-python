"""zip() on firmware data: pairing, strict lengths, unzipping, neighbours and lost items.

Run:   python zip_usage.py
"""

import itertools
import struct
from itertools import pairwise, zip_longest

# ---- 1. Pair two parallel lists, like one index into two C arrays ----
names = ["CTRL", "STATUS", "DATA"]
addrs = [0x00, 0x04, 0x08]
for name, addr in zip(names, addrs):
    print(f"{name:<7}0x{addr:02X}")

# ---- 2. Different lengths: the default stops quietly, strict=True raises ----
limits = [3.3, 1.8]  # one limit is missing
print(list(zip(names, limits)))
try:
    list(zip(names, limits, strict=True))
except ValueError as err:
    print(f"strict=True -> ValueError: {err}")
print(list(zip_longest(names, limits, fillvalue=None)))

# ---- 3. A lookup table from two lists ----
by_name = dict(zip(names, addrs, strict=True))
print(by_name)

# ---- 4. Name the fields of a packed frame ----
FIELDS = ("seq", "temp_dc", "mv", "status")
frame = struct.pack("<HhHB", 7, -125, 3301, 0x80)
print(dict(zip(FIELDS, struct.unpack("<HhHB", frame), strict=True)))

# ---- 5. Unzip: zip(*pairs) turns rows into columns and back ----
samples = [(0, 512), (1, 530), (2, 498)]
times, counts = zip(*samples)
print(times, counts)
print(list(zip(*[(1, 2, 3), (4, 5, 6)])))  # transpose a 2 x 3 table

# ---- 6. Neighbours: differences, steps and sorted checks ----
adc = [100, 104, 103, 110, 110]
print([b - a for a, b in zip(adc, adc[1:])])  # noqa: RUF007  (the older form)
print([b - a for a, b in pairwise(adc)])
print("non-decreasing:", all(a <= b for a, b in pairwise(adc)))

# ---- 7. Pair up bytes into 16-bit words (two ways) ----
raw = bytes([0x34, 0x12, 0x78, 0x56])
print([hex(lo | hi << 8) for lo, hi in zip(raw[0::2], raw[1::2])])
print([hex(lo | hi << 8) for lo, hi in itertools.batched(raw, 2)])

# ---- 8. min and max over a pair: the value picks the name ----
rails = ["3V3", "1V8", "1V0"]
volts = [3.31, 1.79, 0.93]
print(max(zip(volts, rails)), min(zip(volts, rails))[1])

# ---- 9. zip is lazy and gives one pass ----
pairs = zip(names, addrs)
print(list(pairs), list(pairs))

# ---- 10. An iterator that zip reads first loses one item ----
source = iter(range(10, 15))
print(list(zip(source, "ab")), "next:", next(source))
source = iter(range(10, 15))
print(list(zip("ab", source)), "next:", next(source))
