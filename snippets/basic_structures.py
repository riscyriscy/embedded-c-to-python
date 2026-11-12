"""Basic data structures side by side. Run: python3 basic_structures.py"""

# ---- list: growable array. Mutating methods return None ----
adc = [512, 530, 498]
adc.append(505)  # add at the end
adc.extend([510, 0])  # add several
adc.insert(0, 500)  # O(n): shifts the rest, like memmove
removed = adc.pop()  # remove and return the last item
adc.remove(498)  # remove the first item equal to 498
print(adc, removed, adc.index(530), adc.count(505), len(adc))
print(sorted(adc), adc, sorted(adc, reverse=True)[:2])  # sorted() copies; adc.sort() sorts in place
adc.sort(key=lambda s: abs(s - 512))  # sort by distance from mid-scale
print(adc)

# ---- slicing: start:stop:step, stop is excluded, negative counts from the end ----
data = list(range(10))
print(data[2:5], data[:3], data[-3:], data[::3], data[::-1][:3])
data[2:5] = [99]  # a slice can be replaced by a different number of items
del data[0]
print(data)

# ---- copies: assignment makes a second name, not a second list ----
alias = adc
shallow = adc.copy()
alias.append(1)
print(len(adc), len(shallow))
grid = [[0] * 3 for _ in range(2)]  # build rows separately; [[0] * 3] * 2 would repeat one row
grid[0][1] = 7
print(grid)

# ---- tuple: fixed-size record. Unpacking, swapping, star-unpacking ----
version = (1, 10, 0)
major, minor, patch = version
first, *middle, last = [10, 20, 30, 40, 50]
a, b = 1, 2
a, b = b, a  # swap without a temporary
print(major, minor, patch, first, middle, last, a, b, version[1:], version < (1, 9, 3))
single = (5,)  # the comma makes the tuple, not the parentheses
print(type(single).__name__, type((5)).__name__, len(()))  # noqa: UP003, UP034

# ---- set: unique members, fast membership, algebra ----
seen = {3, 1, 3, 2}  # noqa: B033 (the duplicate 3 is the point)
print(seen, 2 in seen, seen | {9}, seen & {1, 9}, seen - {1}, seen ^ {1, 9})
distinct = len(set([512, 512, 530]))  # noqa: C405
print(set("abc") == set("cba"), distinct, {1, 2} <= seen)
frozen = frozenset({1, 2})  # hashable, so usable as a dict key
print({frozen: "pair"})
empty_dict: dict[str, int] = {}
empty_set: set[int] = set()  # {} is a dict, so an empty set needs set()
print(type(empty_dict).__name__, type(empty_set).__name__)

# ---- choosing by cost: membership in a list is O(n), in a set or dict O(1) ----
allowed_list = list(range(1000))
allowed_set = set(allowed_list)
print(999 in allowed_list, 999 in allowed_set)

# ---- nesting, and common built-ins over sequences ----
boards = {"rev1": [3.30, 3.28], "rev2": [3.31, 3.33, 3.32]}
print({k: round(sum(v) / len(v), 3) for k, v in boards.items()})
print(min(shallow), max(shallow), sum(shallow), list(reversed(range(3))), list(zip("ab", (1, 2))))
