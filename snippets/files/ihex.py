"""Intel HEX: write, read with checksum checks, convert to .bin, hexdump. Run: python3 ihex.py"""

from __future__ import annotations

import zlib
from pathlib import Path

OUT = Path("out")


class HexError(ValueError):
    pass


def record(rtype: int, addr: int, data: bytes = b"") -> str:
    body = bytes([len(data), addr >> 8 & 0xFF, addr & 0xFF, rtype]) + data
    checksum = -sum(body) & 0xFF  # two's complement of the byte sum
    return f":{body.hex().upper()}{checksum:02X}"


def write_hex(path: Path, image: dict[int, bytes], width: int = 16) -> None:
    lines: list[str] = []
    upper = -1
    for base, data in sorted(image.items()):
        for off in range(0, len(data), width):
            addr = base + off
            if addr >> 16 != upper:  # type 04: extended linear address (upper 16 bits)
                upper = addr >> 16
                lines.append(record(0x04, 0, upper.to_bytes(2, "big")))
            lines.append(record(0x00, addr & 0xFFFF, data[off : off + width]))
    lines.append(record(0x01, 0))  # end of file
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def read_hex(path: Path) -> dict[int, bytes]:
    """Returns {start: data}: contiguous runs of bytes. Handles types 00, 01, 04 and 05 only."""
    memory: dict[int, int] = {}
    upper = 0
    seen_eof = False
    with path.open(encoding="ascii") as f:
        for n, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            if not line.startswith(":"):
                raise HexError(f"line {n}: missing ':'")
            try:
                raw = bytes.fromhex(line[1:])
            except ValueError:
                raise HexError(f"line {n}: non-hex characters") from None
            if len(raw) < 5:  # length, 2 address bytes, type and checksum are always present
                raise HexError(f"line {n}: record too short")
            if sum(raw) & 0xFF:
                raise HexError(f"line {n}: checksum error")
            length, addr, rtype, data = raw[0], int.from_bytes(raw[1:3], "big"), raw[3], raw[4:-1]
            if len(data) != length:
                raise HexError(f"line {n}: length field {length} but {len(data)} data bytes")
            if rtype == 0x00:
                for i, b in enumerate(data):
                    memory[(upper << 16) + addr + i] = b
            elif rtype == 0x04 and length == 2:
                upper = int.from_bytes(data, "big")
            elif rtype == 0x05 and length == 4:
                pass  # start address (entry point): checked, not needed for a flat image
            elif rtype == 0x01 and length == 0:
                seen_eof = True
                break
            else:  # includes 02 and 03 (segment addressing), which would put data at wrong addresses
                raise HexError(f"line {n}: unsupported record type {rtype:02X} or bad length")
    if not seen_eof:
        raise HexError("no end-of-file record (truncated file?)")
    runs: dict[int, bytearray] = {}  # bytearray.append is O(1); bytes += copies the whole run
    start = prev = -2
    for a in sorted(memory):
        if a != prev + 1:
            start = a
            runs[start] = bytearray()
        runs[start].append(memory[a])
        prev = a
    return {s: bytes(d) for s, d in runs.items()}


def hexdump(data: bytes, base: int, rows: int = 4) -> None:
    for off in range(0, min(len(data), rows * 16), 16):
        chunk = data[off : off + 16]
        ascii_ = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print(f"  {base + off:08X}  {chunk[:8].hex(' '):<23}  {chunk[8:].hex(' '):<23}  |{ascii_}|")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    vectors = (0x2002_0000).to_bytes(4, "little") + (0x0800_0101).to_bytes(4, "little")
    app = vectors + b"\x00" * 8 + b"TLM-100 fw v1.10.0\x00" + bytes(range(64))
    config = b"CFG1" + (250).to_bytes(2, "little")  # in a separate flash sector
    write_hex(OUT / "fw.hex", {0x0800_0000: app, 0x0801_F800: config})
    print("first lines of fw.hex:", *(OUT / "fw.hex").read_text().splitlines()[:3], sep="\n  ")

    segments = read_hex(OUT / "fw.hex")
    print(f"\n{'segment':<8}{'start':>12}{'end':>12}{'bytes':>8}{'crc32':>12}")
    for i, (start, data) in enumerate(segments.items()):
        print(
            f"{i:<8}{start:>#12x}{start + len(data) - 1:>#12x}{len(data):>8}"
            f"{zlib.crc32(data):>#12x}"
        )

    # Flat binary for a flasher: one file from the lowest address, gaps filled with 0xFF
    lo = min(segments)
    hi = max(s + len(d) for s, d in segments.items())
    flat = bytearray(b"\xff" * (hi - lo))
    for start, data in segments.items():
        flat[start - lo : start - lo + len(data)] = data
    (OUT / "fw.bin").write_bytes(flat)
    print(f"\nwrote {OUT / 'fw.bin'}: {len(flat)} bytes from {lo:#x} (gaps = 0xFF)")
    hexdump(bytes(flat), lo)

    # Corrupted or unsupported files must be rejected with a useful message
    lines = (OUT / "fw.hex").read_text().splitlines()
    corrupt = lines.copy()
    corrupt[3] = corrupt[3][:-2] + "00"
    segment_addr = [record(0x02, 0, (0x1000).to_bytes(2, "big")), *lines[1:]]
    cases = {
        "bad.hex": corrupt,
        "truncated.hex": lines[:-1],  # last line is the EOF record
        "segment.hex": segment_addr,
        "short.hex": [":", *lines],
    }
    print()
    for name, content in cases.items():
        (OUT / name).write_text("\n".join(content) + "\n")
        try:
            read_hex(OUT / name)
        except HexError as e:
            print(f"{name} rejected: {e}")


if __name__ == "__main__":
    main()
