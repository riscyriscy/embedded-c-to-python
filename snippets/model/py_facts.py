"""What Python does with the same facts, and what an object costs. Run: python3 py_facts.py"""

import ctypes
import math
import sys
from array import array
from collections.abc import Callable
from typing import Any

C_TYPES = {
    "short": ctypes.c_short,
    "int": ctypes.c_int,
    "long": ctypes.c_long,
    "void*": ctypes.c_void_p,
}
print("ctypes.sizeof:", ", ".join(f"{name} {ctypes.sizeof(t)}" for name, t in C_TYPES.items()))

OBJECTS = {"0": 0, "2**30": 2**30, "2**64": 2**64, "1.0": 1.0, "'a'": "a", "b'a'": b"a", "[]": []}
print("sys.getsizeof:", ", ".join(f"{name} {sys.getsizeof(v)}" for name, v in OBJECTS.items()))

as_list, as_array, as_bytes = [0] * 1000, array("H", [0] * 1000), bytearray(2000)
print(
    f"1000 values: list {sys.getsizeof(as_list)} bytes (pointers only), "
    f"array('H') {sys.getsizeof(as_array)} bytes, bytearray(2000) {sys.getsizeof(as_bytes)} bytes"
)

print(f"-7 // 2 = {-7 // 2}  -7 % 2 = {-7 % 2}  7 // 2 = {7 // 2}  1 / 2 = {1 / 2}")
print(f"int(-7 / 2) = {int(-7 / 2)}  math.fmod(-7, 2) = {math.fmod(-7, 2)}")
print(f"250 + 10 = {250 + 10}  (250 + 10) & 0xFF = {(250 + 10) & 0xFF}")
print(f"0x10000 & 0xFFFF = {0x10000 & 0xFFFF}")
product = 4_000_000_000 * 3
print(f"4000000000 * 3 = {product}  masked to 32 bits = {product & 0xFFFFFFFF}")

x, y = 1, 2
x, y = y, x  # no temporary: the right side is evaluated first
print("swapped: x =", x, "y =", y)

a = [1, 2, 3]
b = a  # a second name for the same list, not a copy
b.append(4)
print("a =", a, " a is b:", a is b, " list(a) is a:", list(a) is a)

text: Any = "1"  # Any, so that mypy lets the deliberate mistake through
checks: list[tuple[str, Callable[[], object]]] = [
    ("a[10]", lambda: a[10]),
    ("1 // 0", lambda: 1 // 0),
    ("'1' + 1", lambda: text + 1),
]
for label, fn in checks:
    try:
        fn()
    except (IndexError, ZeroDivisionError, TypeError) as exc:
        print(f"{label:8} -> {type(exc).__name__}: {exc}")
