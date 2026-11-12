"""Dictionaries in use. Run: python3 dictionaries.py"""

from collections import defaultdict
from collections.abc import Callable

# ---- create, read, update, delete ----
registers = {"CTRL": 0x00, "STATUS": 0x04}
registers["DATA"] = 0x08  # insert
registers.update(IRQ_EN=0x0C, IRQ_ST=0x10)  # several at once
print(registers)
print(registers["STATUS"], registers.get("MISSING"), registers.get("MISSING", -1))
try:
    missing = registers["MISSING"]
except KeyError as exc:
    print(f"KeyError: {exc}")
print("CTRL" in registers, "ctrl" in registers, len(registers))
print(registers.pop("IRQ_ST"), registers.pop("NOPE", None), list(registers))

# ---- iterate: keys, values, items; insertion order is kept ----
for reg_name, offset in registers.items():
    print(f"  {reg_name:<7}{offset:#04x}")
print(sum(registers.values()), max(registers, key=lambda k: registers[k]))

# ---- merge, comprehension, invert, build from two lists ----
defaults = {"baud": 115200, "parity": "N", "timeout": 1.0}
overrides = {"baud": 921600, "rtscts": True}
config = defaults | overrides  # right-hand side wins
print(config)
by_offset = {offset: reg_name for reg_name, offset in registers.items()}
print(by_offset)
print(dict(zip(["a", "b", "c"], [1, 2, 3])), {n: n * n for n in range(4)})
print(defaults.keys() & overrides.keys(), sorted(config.items(), key=lambda kv: str(kv[0]))[:2])

# ---- counting and grouping ----
log = ["CRC", "TIMEOUT", "CRC", "OK", "CRC", "OK"]
counts: dict[str, int] = {}
for event in log:
    counts[event] = counts.get(event, 0) + 1  # the plain-dict idiom
print(counts)
groups: defaultdict[int, list[str]] = defaultdict(list)
for event in log:
    groups[len(event)].append(event)  # missing key starts as an empty list
print(dict(groups))
print(counts.setdefault("NAK", 0), counts)

# ---- keys must be hashable; mutable keys are rejected ----
try:
    bad_key = {[1, 2]: "x"}
except TypeError:
    print("TypeError: a list cannot be a dict key")
pins = {(0, 9): "UART0_TX", (0, 10): "UART0_RX"}  # (port, pin) tuple as a key
print(pins[(0, 9)])

# ---- a dict of functions replaces a switch ----
HANDLERS: dict[str, Callable[[int], str]] = {
    "double": lambda n: str(n * 2),
    "hex": lambda n: f"{n:#x}",
}
for op in ("double", "hex", "oct"):
    handler = HANDLERS.get(op)
    print(op, "->", handler(255) if handler else "unknown op")

# ---- changing a dict while iterating over it is an error ----
try:
    for reg_name in registers:
        if reg_name.startswith("IRQ"):
            del registers[reg_name]
except RuntimeError as exc:
    print(f"RuntimeError: {exc}")
registers = {k: v for k, v in registers.items() if not k.startswith("IRQ")}  # build a new dict
print(registers)
