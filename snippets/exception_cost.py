"""Cost of a missing key: 'in' check versus try/except. Run: python3 exception_cost.py"""

from timeit import repeat

table = {"a": 1}
N = 1_000_000


def check_present() -> int:
    return table["a"] if "a" in table else 0  # noqa: SIM401


def check_missing() -> int:
    return table["b"] if "b" in table else 0  # noqa: SIM401


def try_present() -> int:
    try:
        return table["a"]
    except KeyError:
        return 0


def try_missing() -> int:
    try:
        return table["b"]
    except KeyError:
        return 0


for label, fn in (
    ("if 'in', key present", check_present),
    ("if 'in', key missing", check_missing),
    ("try/except, key present", try_present),
    ("try/except, key missing", try_missing),
):
    best = min(repeat(fn, number=N, repeat=5))
    print(f"{label:26}{best / N * 1e9:7.0f} ns per call")
