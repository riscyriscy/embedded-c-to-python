"""Identity (is) versus equality (==). Run: python3 identity.py"""

import math
from dataclasses import dataclass

# ---- == asks "do the values match?", is asks "is it the same object?" ----
a = [1, 2, 3]
b = [1, 2, 3]
c = a
print(a == b, a is b, a == c, a is c, id(a) == id(c))
c.append(4)  # c is another name for the same list
print(a, b, a is c)


# ---- is cannot be overridden, == calls __eq__ ----
@dataclass
class Sample:
    channel: int
    raw: int


s1, s2 = Sample(1, 512), Sample(1, 512)
print(s1 == s2, s1 is s2)  # a dataclass compares its fields


class AlwaysEqual:
    def __eq__(self, other: object) -> bool:
        return True

    __hash__ = None  # type: ignore[assignment]  # a class that defines __eq__ must say how it hashes


odd = AlwaysEqual()
print(odd == 42, odd == None, odd is None)  # == can be fooled, is cannot

# ---- None, True and False are single objects: test them with is ----
result: int | None = 0
print(result == None, result is None, not result)
zero, one = 0, 1
print(zero == False, zero is False, one == True, one is True)
flag = 2
print(flag == True, bool(flag), flag is True)

# ---- identity of ints and strings is an implementation detail ----
small1, small2 = int("200"), int("200")
big1, big2 = int("100000"), int("100000")
print(small1 is small2, big1 is big2, big1 == big2)  # CPython caches -5 to 256
text1, text2 = "ab,c".replace(",", ""), "a,bc".replace(",", "")
print(text1 == text2, text1 is text2)  # equal strings built at run time are separate objects

# ---- NaN is not equal to itself, but it is the same object ----
nan = float("nan")
print(
    nan == nan,  # noqa: PLR0124
    nan is nan,  # noqa: PLR0124
    math.isnan(nan),
    [nan] == [nan],
    [float("nan")] == [float("nan")],
)

# ---- a sentinel: a unique object that no real value can equal ----
_MISSING = object()


def lookup(table: dict[str, int | None], key: str, default: object = _MISSING) -> object:
    value = table.get(key, _MISSING)
    if value is _MISSING:  # None is a legal value here, so it cannot mean "absent"
        if default is _MISSING:
            raise KeyError(key)
        return default
    return value


table: dict[str, int | None] = {"gain": 4, "offset": None}
print(lookup(table, "offset"), lookup(table, "mode", "auto"))

# ---- copies: == compares contents, is shows whether the copy is separate ----
nested = [[1, 2], [3]]
shallow = nested.copy()
print(shallow == nested, shallow is nested, shallow[0] is nested[0])
