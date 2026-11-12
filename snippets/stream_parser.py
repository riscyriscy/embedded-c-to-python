"""Parse frames from a byte stream that arrives in pieces. Run: python3 stream_parser.py"""

import binascii
import random
import struct

SYNC = 0xA5
HEADER = struct.Struct("<BBHI")  # sync, type, length, seq
CRC = struct.Struct("<H")
SAMPLE = struct.Struct("<Hh")  # channel, value
MAX_PAYLOAD = 512  # a corrupt length must not make the parser wait for 64 KiB

Frame = tuple[int, int, bytes]  # type, seq, payload


def crc16(data: bytes | bytearray) -> int:
    return binascii.crc_hqx(data, 0xFFFF)  # CRC-16/CCITT-FALSE, as in Phase 1


def build(msg_type: int, seq: int, payload: bytes) -> bytes:
    """Header, payload and CRC, written in place into one bytearray."""
    end = HEADER.size + len(payload)
    buf = bytearray(end + CRC.size)
    HEADER.pack_into(buf, 0, SYNC, msg_type, len(payload), seq)
    buf[HEADER.size : end] = payload
    CRC.pack_into(buf, end, crc16(buf[:end]))
    return bytes(buf)


class StreamParser:
    def __init__(self) -> None:
        self.buf = bytearray()
        self.dropped = 0  # bytes skipped while looking for a frame

    def _drop(self, count: int) -> None:
        del self.buf[:count]
        self.dropped += count

    def feed(self, data: bytes) -> list[Frame]:
        """Add what a read returned and return every complete frame, however the bytes were split."""
        self.buf += data
        frames: list[Frame] = []
        while True:
            start = self.buf.find(SYNC)
            if start < 0:
                self._drop(len(self.buf))  # no sync byte: all of it is noise
                return frames
            self._drop(start)
            if len(self.buf) < HEADER.size:
                return frames  # header incomplete: wait for the next read
            _, msg_type, length, seq = HEADER.unpack_from(self.buf)
            if length > MAX_PAYLOAD:
                self._drop(1)  # not a real header: try the next sync byte
                continue
            end = HEADER.size + length
            if len(self.buf) < end + CRC.size:
                return frames  # body incomplete: wait
            if CRC.unpack_from(self.buf, end)[0] != crc16(self.buf[:end]):
                self._drop(1)  # false sync or damaged frame: resync from the next byte
                continue
            frames.append((msg_type, seq, bytes(self.buf[HEADER.size : end])))
            del self.buf[: end + CRC.size]


def run(chunks: list[bytes]) -> tuple[list[Frame], int]:
    parser = StreamParser()
    frames: list[Frame] = []
    for chunk in chunks:
        frames += parser.feed(chunk)
    return frames, parser.dropped


def main() -> None:
    samples = b"".join(SAMPLE.pack(ch, v) for ch, v in [(1, 2845), (2, -40), (3, 3300)])
    damaged = bytearray(build(2, 12, b"damaged"))
    damaged[9] ^= 0x01  # one flipped bit in the payload
    stream = (
        b"\x00\xa5\x07\xff\xff"  # noise, ending in a false header with length 0xFFFF
        + build(1, 10, samples)
        + build(2, 11, b"\xa5\xa5 sync bytes inside the payload")
        + bytes(damaged)
        + build(1, 13, SAMPLE.pack(4, 0))
    )
    whole, dropped = run([stream])
    print(
        f"all at once: {len(whole)} frames, seqs {[f[1] for f in whole]}, {dropped} bytes dropped"
    )
    print("samples in frame 10:", list(SAMPLE.iter_unpack(whole[0][2])))
    print("payload of frame 11:", whole[1][2])
    one_by_one = run([stream[i : i + 1] for i in range(len(stream))])
    print("one byte per read: same result:", one_by_one == (whole, dropped))
    rng = random.Random(7)
    same = 0
    for _ in range(200):
        chunks, pos = [], 0
        while pos < len(stream):
            step = rng.randint(1, 9)
            chunks.append(stream[pos : pos + step])
            pos += step
        same += run(chunks) == (whole, dropped)
    print(f"200 random splits into 1 to 9 byte reads: {same} same result")


if __name__ == "__main__":
    main()
