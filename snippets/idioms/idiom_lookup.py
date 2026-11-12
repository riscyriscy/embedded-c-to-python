"""C habit versus Python idiom: register lookup. Run: python3 idiom_lookup.py"""

from dataclasses import dataclass

NAMES = ["CTRL", "STATUS", "DATA", "IRQ_EN", "IRQ_ST"]  # parallel arrays, as in C
ADDRS = [0x00, 0x04, 0x08, 0x0C, 0x10]
RESETS = [0x0000, 0x0001, 0x0000, 0x0000, 0x0000]


def find_c_style(name: str) -> int:
    """Linear search that returns an index, or -1 for not found."""
    found = -1
    for i in range(len(NAMES)):
        if NAMES[i] == name:
            found = i
            break
    return found


def describe_c_style(name: str) -> str:
    i = find_c_style(name)
    if i < 0:
        return f"{name}: not found"
    return f"{name}: address {ADDRS[i]:#04x}, reset {RESETS[i]:#06x}"


@dataclass(frozen=True)
class Register:
    name: str
    addr: int
    reset: int


REGISTERS = [Register(n, a, r) for n, a, r in zip(NAMES, ADDRS, RESETS, strict=True)]
BY_NAME = {reg.name: reg for reg in REGISTERS}  # built once; each lookup is a hash probe
BY_ADDR = {reg.addr: reg for reg in REGISTERS}


def describe_pythonic(name: str) -> str:
    reg = BY_NAME.get(name)  # None when absent, so there is no magic -1
    if reg is None:
        return f"{name}: not found"
    return f"{reg.name}: address {reg.addr:#04x}, reset {reg.reset:#06x}"


for n in ("STATUS", "DMA"):
    print(
        describe_c_style(n),
        "|",
        describe_pythonic(n),
        "|",
        describe_c_style(n) == describe_pythonic(n),
    )
print("register at 0x0C:", BY_ADDR[0x0C].name)
print(
    "first register with a non-zero reset:",
    next((reg.name for reg in REGISTERS if reg.reset), None),
)
print(
    "by address, highest first:",
    [reg.name for reg in sorted(REGISTERS, key=lambda r: r.addr, reverse=True)],
)
