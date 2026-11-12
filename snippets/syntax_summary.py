"""Checks every claim in the syntax summary tables of Phase 1.

Run:   python syntax_summary.py
Prints one line per table and exits with status 1 if any check fails.
"""

import io
import math
import sys
from dataclasses import dataclass
from enum import IntEnum, IntFlag

failed: list[str] = []
counts: dict[str, int] = {}


def check(table: str, label: str, ok: bool) -> None:
    counts[table] = counts.get(table, 0) + 1
    if not ok:
        failed.append(f"{table}: {label}")


# Table 1: basic types and literals
T = "types"
literals = [0x2A, 0b101010, 0o52, 42]
check(T, "int literals", len(set(literals)) == 1 and 1_000_000 == 10**6)
check(T, "int never wraps", 2**64 + 1 > 2**64 and (255 + 1).bit_length() == 9)
small = 1e-3
check(T, "float", small == 0.001 and math.isinf(float("inf")) and math.isnan(float("nan")))
check(T, "float is not exact", 0.1 + 0.2 != 0.3)
check(T, "complex", (2 + 3j).imag == 3.0 and abs(3 + 4j) == 5.0)
check(T, "bool is an int", isinstance(True, int) and True + True == 2)
nothing = None
check(T, "None is a single object", nothing is None and not nothing)
check(T, "str", len("µC") == 2 and len("µC".encode()) == 3 and len(r"\d") == 2)
check(T, "f-string", f"{255:#04x}" == "0xff" and f"{3.14159:.2f}" == "3.14")
check(T, "bytes", b"\x01\x02"[0] == 1 and b"\x01\x02"[0:1] == b"\x01")
check(T, "bytearray", bytearray(2) == bytearray(b"\x00\x00"))
check(T, "range", list(range(0, 10, 3)) == [0, 3, 6, 9] and len(range(10)) == 10)

# Table 2: containers
lst = [1, 2, 3]
tup = (1, 2, 3)
dct = {"a": 1}
st = {1, 2, 3}
C = "containers"
empty_set: set[int] = set()
empty = (len([]), len(()), len({}), len(empty_set))
check(C, "empty", empty == (0, 0, 0, 0) and type({}) is dict and type(empty_set) is set)
five = 5
check(C, "one item", type((5,)) is tuple and type(five) is int and len([5]) == 1)
check(C, "read", lst[0] == 1 and lst[-1] == 3 and tup[-1] == 3 and dct["a"] == 1)
check(C, "dict get", dct.get("z", 0) == 0 and dct.get("z") is None)
check(C, "slice", lst[1:3] == [2, 3] and tup[1:] == (2, 3) and lst[::-1] == [3, 2, 1])
a = [1, 2, 3]
a.append(4)
d = {"a": 1}
d["b"] = 2
s = {1, 2, 3}
s.add(4)
check(C, "add", a == [1, 2, 3, 4] and d == {"a": 1, "b": 2} and s == {1, 2, 3, 4})
a.remove(2)
del a[0]
del d["a"]
s.discard(9)
s.discard(1)
check(C, "remove", a == [3, 4] and d == {"b": 2} and s == {2, 3, 4})
try:
    tup[0] = 9  # type: ignore[index]
except TypeError:
    tup_immutable = True
else:
    tup_immutable = False
check(C, "tuple is immutable", tup_immutable)
check(C, "membership", 2 in lst and 2 in tup and "a" in dct and 2 in st and 9 not in st)
check(C, "len", len(lst) == len(tup) == len(dct) + 2 == len(st))
check(C, "iterate", [k for k, v in dct.items()] == ["a"] and [x for x in st] == [1, 2, 3])
check(
    C,
    "combine",
    [1] + [2] == [1, 2]
    and (1,) + (2,) == (1, 2)
    and {"a": 1} | {"b": 2} == {"a": 1, "b": 2}
    and {1, 2} | {2, 3} == {1, 2, 3},
)
check(
    C,
    "set algebra",
    {1, 2} & {2, 3} == {2} and {1, 2} - {2, 3} == {1} and {1, 2} ^ {2, 3} == {1, 3},
)
check(
    C,
    "comprehensions",
    [x * 2 for x in lst] == [2, 4, 6]
    and {k: k * k for k in lst} == {1: 1, 2: 4, 3: 9}
    and {x % 2 for x in lst} == {0, 1}
    and tuple(x for x in lst) == tup,
)
first, *rest = lst
check(C, "unpack", first == 1 and rest == [2, 3] and {**dct, "c": 3} == {"a": 1, "c": 3})
set_first, *set_rest = st
check(C, "set unpack, any order", sorted([set_first, *set_rest]) == [1, 2, 3])
check(
    C,
    "hashable keys",
    {(1, 2): "pair"}[(1, 2)] == "pair" and frozenset({1}) in {frozenset({1})},
)

check(C, "dict pop", {"a": 1}.pop("a") == 1 and tup[0:1] + (9,) == (1, 9))
p, q, r = tup
check(C, "tuple unpack", (p, q, r) == (1, 2, 3))

# Table 3: statements and operators
S = "statements"
x, y = 1, 2
x, y = y, x
check(S, "swap", (x, y) == (2, 1))
check(S, "ternary", ("hi" if x > 1 else "lo") == "hi")
ten = 10
check(S, "chained compare", 0 <= x < 10 and not (0 <= ten < 10))
check(
    S,
    "division",
    7 // 2 == 3 and -7 // 2 == -4 and -7 % 2 == 1 and 7 / 2 == 3.5 and 2**10 == 1024,
)
check(
    S,
    "bit operators",
    (0xF0 & 0x3C, 0xF0 | 0x0F, 0xF0 ^ 0xFF, ~0 & 0xFF, 1 << 4, 0x80 >> 7)
    == (0x30, 0xFF, 0x0F, 0xFF, 16, 1),
)
zero = 0
check(S, "logic keywords", (x > 0 and not y > 5) and (zero or "x") == "x")
n = 0
n += 5
check(S, "augmented assignment", n == 5)
total = 0
for i, v in enumerate([10, 20], start=1):
    total += i * v
check(S, "enumerate", total == 50)
check(S, "zip strict", list(zip("ab", [1, 2], strict=True)) == [("a", 1), ("b", 2)])
found = None
for v in [3, 5, 7]:
    if v == 5:
        found = v
        break
else:
    found = -1
check(S, "for else", found == 5)
if (m := len("abc")) > 2:
    walrus_ok = m == 3
else:
    walrus_ok = False
check(S, "walrus", walrus_ok)


def f(a: int, b: int = 1, *, c: int = 2) -> int:
    return a + b + c


check(S, "def with defaults", f(1) == 4 and f(1, 2, c=3) == 6)
check(S, "lambda", sorted(["bb", "a"], key=lambda s: len(s)) == ["a", "bb"])
try:
    raise ValueError("bad")
except ValueError as e:
    caught = str(e)
finally:
    done = True
check(S, "try", caught == "bad" and done)
match [0x7E, 3]:
    case [0x7E, length]:
        matched = length
    case _:
        matched = -1
check(S, "match", matched == 3)

empty_list: list[int] = []
check(S, "truthiness", not empty_list and not 0 and not None and not "" and bool([0]))
node = None
check(S, "guard", not (node and node.ready))  # no AttributeError: `and` stops at None
check(S, "several values", 2 in (1, 2, 3) and 5 not in (1, 2, 3))
values = [3, 12, 7]
check(S, "any and all", any(v > 9 for v in values) and all(v > 0 for v in values))
rate = 0
check(S, "or returns an operand", (zero or "x") == "x" and ("a" and "b") == "b")
check(S, "default value", (rate or 100) == 100 and (100 if rate is None else rate) == 0)


@dataclass
class Sample:
    t: int
    v: int


check(S, "dataclass", Sample(1, 2) == Sample(1, 2) and Sample(1, 2).v == 2)
with io.StringIO("line") as stream:
    text = stream.read()
check(S, "with", text == "line" and stream.closed)


class State(IntEnum):
    IDLE = 0
    ARMED = 1


class Ctrl(IntFlag):
    IRQ = 1
    DMA = 4


check(
    S,
    "enum",
    int(State.ARMED) == 1 and State(1) is State.ARMED and State["ARMED"] is State.ARMED,
)
check(
    S,
    "enum name and iteration",
    State.IDLE.name == "IDLE" and [m.name for m in State] == ["IDLE", "ARMED"],
)
check(S, "int flags", int(Ctrl.DMA | Ctrl.IRQ) == 5 and Ctrl.DMA in (Ctrl.DMA | Ctrl.IRQ))

check(
    S,
    "int flag text",
    f"{Ctrl.DMA}" == "4" and repr(Ctrl.DMA) == "<Ctrl.DMA: 4>" and Ctrl.DMA.name == "DMA",
)


def c_div(a: int, b: int) -> tuple[int, int]:
    """Quotient and remainder as C computes them: the quotient truncates toward zero."""
    q = abs(a) // abs(b)
    q = -q if (a < 0) != (b < 0) else q
    return q, a - q * b


big = -(2**60 + 1)
check(
    S,
    "C division",
    c_div(-7, 2) == (-3, -1)
    and c_div(7, -2) == (-3, 1)
    and c_div(big, 1) == (big, 0)
    and int(big / 1) != big
    and math.fmod(-7, 2) == -1.0,
)

for name, n_checks in counts.items():
    print(f"{name}: {n_checks} checks")
if failed:
    print("FAILED:", *failed, sep="\n  ")
    sys.exit(1)
print("all checks passed")
