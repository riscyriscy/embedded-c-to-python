"""Late binding in lambdas and callback tables. Run: python3 late_binding.py"""

from collections.abc import Callable
from functools import partial

REGISTERS = ["CTRL", "STATUS", "DATA"]
log: list[str] = []


def write_reg(index: int, value: int) -> None:
    log.append(f"{REGISTERS[index]} <- {value:#04x}")


# ---- the closure holds the variable i, not the value i had when it was created ----
bad: list[Callable[[], int]] = [lambda: i for i in range(3)]  # noqa: B023
print("lambda: i          ->", [f() for f in bad])
by_default: list[Callable[..., int]] = [lambda i=i: i for i in range(3)]
print("lambda i=i: i      ->", [f() for f in by_default])
by_partial: list[Callable[[], int]] = [partial(int, i) for i in range(3)]
print("partial(int, i)    ->", [f() for f in by_partial])

# ---- the same trap in a dispatch table, one handler per register index ----
Handler = Callable[[int], None]
bad_table: dict[int, Handler] = {}
good_table: dict[int, Handler] = {}
for index in range(len(REGISTERS)):
    bad_table[index] = lambda value: write_reg(index, value)  # noqa: B023
    good_table[index] = partial(write_reg, index)

for name, table in [("lambda value", bad_table), ("partial", good_table)]:
    log.clear()
    for reg, handler in table.items():
        handler(0x10 + reg)
    print(f"{name:<12} writes:", log)


# ---- a factory function gives each handler its own variable ----
def make_handler(index: int) -> Handler:
    def handler(value: int) -> None:
        write_reg(index, value)

    return handler


factory_table = {index: make_handler(index) for index in range(len(REGISTERS))}
log.clear()
factory_table[1](0x55)
print("factory      writes:", log)
