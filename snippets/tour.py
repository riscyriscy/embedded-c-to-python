"""Python for a C programmer: run with python3 tour.py"""

import struct
from collections.abc import Callable, Iterator
from contextlib import contextmanager

# ---- Integers never overflow: you must mask like the hardware would ----
reg = 0xFFFF
reg += 1
print(f"unmasked: {reg:#x}, as uint16_t: {reg & 0xFFFF:#06x}")
print(f"-1 as uint8: {-1 & 0xFF}, arithmetic shift: {-16 >> 2}")

# ---- bytes (immutable) vs bytearray (mutable) vs memoryview (zero-copy window) ----
buf = bytearray(8)
view = memoryview(buf)[2:6]  # like a pointer + length into buf: no copy
view[0] = 0xAB
print(f"buf after write through view: {buf.hex(' ')}")
print(f"indexing bytes gives int: {b'AB'[0]}, slicing gives bytes: {b'AB'[0:1]!r}")

# ---- struct: packed C layouts. '<' = little-endian, no padding ----
hdr = struct.pack("<BBH", 0x10, 7, 9)
print(f"header bytes: {hdr.hex(' ')}, calcsize('<IhHB') = {struct.calcsize('<IhHB')}")
print(
    f"'<BI' = {struct.calcsize('<BI')} bytes, native 'BI' = {struct.calcsize('BI')} (padding, like a C struct)"
)
be = bytes([0x12, 0x34])
print(f"int.from_bytes big-endian: {int.from_bytes(be, 'big'):#06x}")


# ---- Structural pattern matching on a header (Python 3.10+) ----
# Pitfall: bytes/str never match sequence patterns, so match on a tuple of the ints
def classify(frame: bytes) -> str:
    match tuple(frame):
        case [0xA5, 0x01, *_]:
            return "ping"
        case [0xA5, 0x10, length, *_] if length <= 8:
            return f"telemetry, {length} bytes"
        case [0xA5, *_]:
            return "unknown type"
        case _:
            return "bad sync byte"


print(classify(b"\xa5\x10\x04"), "|", classify(b"\x00\x01"))


# ---- Context managers: deterministic cleanup, like RAII ----
@contextmanager
def fake_port(name: str) -> Iterator[Callable[[str], None]]:
    print(f"{name} opened")
    try:
        yield lambda s: print(f"{name} <- {s}")
    finally:
        print(f"{name} closed")  # runs even if the body raises


with fake_port("ttyUSB0") as write:
    write("hello")


# ---- Generators: a function that pauses, like a coroutine/state machine ----
def frames(stream: bytes) -> Iterator[bytes]:
    start = 0
    for i, b in enumerate(stream):
        if b == 0:
            yield stream[start:i]
            start = i + 1


print(list(frames(b"ab\x00cd\x00")))

# ---- Names are references: assignment never copies a list ----
a = [1, 2, 3]
b = a
b.append(4)
print(f"a is b: {a is b}, a = {a}")
