"""C habit versus Python idiom: CRC-16/CCITT-FALSE. Run: python3 idiom_crc.py"""

import binascii
import time
from collections.abc import Callable

POLY = 0x1021


def crc16_bitwise(data: bytes, crc: int = 0xFFFF) -> int:
    """The textbook loop: 8 shifts per byte, masked to 16 bits because Python ints never wrap."""
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ POLY) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def _make_table() -> list[int]:
    table = []
    for byte in range(256):
        crc = byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ POLY) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
        table.append(crc)
    return table


TABLE = _make_table()


def crc16_table(data: bytes, crc: int = 0xFFFF) -> int:
    """The embedded favourite: one table lookup per byte."""
    for byte in data:
        crc = ((crc << 8) & 0xFFFF) ^ TABLE[(crc >> 8) ^ byte]
    return crc


def crc16_library(data: bytes, crc: int = 0xFFFF) -> int:
    """The standard library already has it, written in C."""
    return binascii.crc_hqx(data, crc)


def best_ms(fn: Callable[[bytes], int], data: bytes) -> float:
    best = min(_elapsed(fn, data) for _ in range(3))
    return best * 1000


def _elapsed(fn: Callable[[bytes], int], data: bytes) -> float:
    start = time.perf_counter()
    fn(data)
    return time.perf_counter() - start


check = b"123456789"
for fn in (crc16_bitwise, crc16_table, crc16_library):
    print(f"{fn.__name__:14} check value {fn(check):#06x}  (the published value is 0x29b1)")

blob = bytes(range(256)) * 256  # 64 KiB
print("all three agree on 64 KiB:", crc16_bitwise(blob) == crc16_table(blob) == crc16_library(blob))
print(
    "incremental: split in two chunks gives the same CRC:",
    crc16_library(blob[32768:], crc16_library(blob[:32768])) == crc16_library(blob),
)
for fn in (crc16_bitwise, crc16_table, crc16_library):
    print(f"{fn.__name__:14} {best_ms(fn, blob):8.2f} ms per 64 KiB")
