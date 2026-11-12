"""A function to step through. Run: python3 pdb_demo.py"""


def checksum(frame: bytes) -> int:
    total = 0
    for byte in frame:
        total = (total + byte) & 0xFF
    breakpoint()  # stops here
    return (-total) & 0xFF


print(checksum(b"\x01\x02\xfe"))
