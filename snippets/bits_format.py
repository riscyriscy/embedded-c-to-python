"""Number formatting and bit manipulation. Run: python3 bits_format.py"""

from enum import IntFlag

# ---- format(), bin(), hex(), oct(), int(s, base) ----
reg = 0xA5
print(bin(reg), hex(reg), oct(reg), int("0b10100101", 0), int("a5", 16))
print(format(reg, "#010b"), format(reg, "08b"), format(reg, "#06x"), format(reg, "X"))
print(f"{reg:>8d}|{reg:<8d}|{reg:^8d}|{reg:+d}|{reg:,}|{1234567:,}|{1234567:_}")
print(f"{3.14159:.3f} {0.000123:e} {1234.5:g} {0.25:.1%} {2**20:,.0f}")
print(f"{reg:#x}".upper(), f"{reg:#010_b}", f"{-reg:#x}", f"{-reg & 0xFF:#04x}")
width = 12
print(f"{reg:0{width}b}", format(reg, f"0{width}b") == f"{reg:0{width}b}")  # nested field
print("{:>6} {:<6}|".format("ab", "cd"), "{0}-{0}-{1}".format("x", "y"))
print(format("txt", "*^9"), format(255, "c") == "\xff", format(True, "d"))

# ---- bitwise operators: & | ^ ~ << >> ----
a, b = 0b1100, 0b1010
print(f"{a & b:04b} {a | b:04b} {a ^ b:04b} {a << 2:08b} {a >> 2:04b}")
print(~a, ~a & 0xF, -1 >> 1, -8 >> 1, (-1) & 0xFFFF)  # ~x is -x-1, >> is arithmetic
print(1 << 100, (1 << 100).bit_length(), (255).bit_count(), (0).bit_length())

# ---- precedence differs from C: comparison binds looser than & ^ | ----
x, mask = 6, 1
print(x & mask == 0, (x & mask) == 0, x & (mask == 0))
print(x & 0b10 != 0, x | 1 << 3, (x | 1) << 3)  # shifts bind tighter than & ^ |

# ---- set, clear, toggle, test, field extract and insert ----
STATUS_READY = 1 << 0
STATUS_ERROR = 1 << 3
FIELD_SHIFT, FIELD_MASK = 4, 0b111  # 3-bit field in bits 6..4
status = 0
status |= STATUS_READY | STATUS_ERROR  # set
status &= ~STATUS_ERROR  # clear: ~ gives a negative int, and & keeps it safe
status ^= STATUS_ERROR  # toggle
print(f"{status:08b}", bool(status & STATUS_READY), (status >> 3) & 1)
status = (status & ~(FIELD_MASK << FIELD_SHIFT)) | (5 << FIELD_SHIFT)  # insert 5
print(f"{status:08b}", (status >> FIELD_SHIFT) & FIELD_MASK)


# ---- fixed width: Python ints never overflow, so mask and sign-extend explicitly ----
def u8(v: int) -> int:
    return v & 0xFF


def sign_extend(v: int, bits: int) -> int:
    sign = 1 << (bits - 1)
    return (v & (sign - 1)) - (v & sign)


def rotl8(v: int, n: int) -> int:
    n %= 8
    return u8(v << n | v >> (8 - n))


def reverse8(v: int) -> int:
    return int(format(v, "08b")[::-1], 2)


print(u8(200 + 100), u8(-1), sign_extend(0xFF, 8), sign_extend(0x7F, 8), sign_extend(0x800, 12))
print(f"{rotl8(0b10010110, 3):08b} {reverse8(0b00000110):08b} {(0b10110).bit_count()}")

# ---- ints to bytes and back ----
word = 0x12345678
print(word.to_bytes(4, "little").hex(" "), word.to_bytes(4, "big").hex(" "))
print(
    hex(int.from_bytes(b"\x78\x56\x34\x12", "little")),
    int.from_bytes(b"\xff\xfe", "big", signed=True),
)
swapped = int.from_bytes(word.to_bytes(4, "little"), "big")  # byte swap, like __builtin_bswap32
print(hex(swapped))


# ---- named flags: IntFlag is an int, so it works with & | ~ and with registers ----
class Ctrl(IntFlag):
    ENABLE = 1
    IRQ = 2
    DMA = 4
    DEFAULT = ENABLE | IRQ


ctrl = Ctrl.DEFAULT | Ctrl.DMA
print(repr(ctrl), int(ctrl), Ctrl.IRQ in ctrl, ctrl & ~Ctrl.IRQ, Ctrl(5), format(ctrl, "03b"))
print(f"{ctrl}", str(Ctrl.DMA), Ctrl.DMA.name, ctrl.name)  # str() is the number, so log .name
reg = 0xFF  # a register read back with its reserved bits 3 to 7 set
print(hex(reg & ~Ctrl.IRQ), hex(reg & ~int(Ctrl.IRQ)))  # ~ on an IntFlag flips only defined bits
