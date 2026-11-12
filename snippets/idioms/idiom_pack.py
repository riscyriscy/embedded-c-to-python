"""C habit versus Python idiom: packing and unpacking a frame header. Run: python3 idiom_pack.py"""

import struct
from dataclasses import dataclass

SYNC = 0xA5


def pack_c_style(msg_type: int, length: int, seq: int) -> bytes:
    """Shift and mask every field into a byte buffer, little-endian."""
    buf = bytearray(8)
    buf[0] = SYNC
    buf[1] = msg_type & 0xFF
    buf[2] = length & 0xFF
    buf[3] = (length >> 8) & 0xFF
    buf[4] = seq & 0xFF
    buf[5] = (seq >> 8) & 0xFF
    buf[6] = (seq >> 16) & 0xFF
    buf[7] = (seq >> 24) & 0xFF
    return bytes(buf)


def unpack_c_style(buf: bytes) -> tuple[int, int, int]:
    if len(buf) < 8 or buf[0] != SYNC:
        raise ValueError("bad header")
    length = buf[2] | (buf[3] << 8)
    seq = buf[4] | (buf[5] << 8) | (buf[6] << 16) | (buf[7] << 24)
    return buf[1], length, seq


HEADER = struct.Struct("<BBHI")  # sync, type, length, seq: no padding with "<"


@dataclass(frozen=True)
class Header:
    msg_type: int
    length: int
    seq: int

    def pack(self) -> bytes:
        return HEADER.pack(SYNC, self.msg_type, self.length, self.seq)

    @classmethod
    def unpack(cls, buf: bytes) -> "Header":
        sync, msg_type, length, seq = HEADER.unpack(buf)  # raises struct.error on a wrong size
        if sync != SYNC:
            raise ValueError("bad header")
        return cls(msg_type, length, seq)


wire = pack_c_style(0x10, 300, 0x01020304)
print("C style bytes: ", wire.hex(" "))
print("struct bytes:  ", Header(0x10, 300, 0x01020304).pack().hex(" "), "| size", HEADER.size)
print("same bytes:    ", wire == Header(0x10, 300, 0x01020304).pack())
print("C style decode:", unpack_c_style(wire))
print("struct decode: ", Header.unpack(wire))
print("one field:     ", int.from_bytes(wire[4:8], "little"))
try:
    Header.unpack(wire[:5])
except struct.error as exc:
    print("short buffer:  ", exc)
