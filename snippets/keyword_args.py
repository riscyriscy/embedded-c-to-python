"""Named (keyword) arguments, defaults, * and /. Run: python3 keyword_args.py"""

import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial


# ---- C style: a long positional list. The call site does not say what each value means ----
def uart_open_positional(
    port: str, baud: int, bits: int, parity: str, stop: int, flow: bool
) -> str:
    return f"{port} {baud} {bits}{parity}{stop} flow={flow}"


print(uart_open_positional("/dev/ttyUSB0", 115200, 8, "N", 1, True))  # which value is True?


# ---- keyword-only parameters: everything after * must be named ----
def uart_open(
    port: str,
    *,
    baud: int = 115200,
    bits: int = 8,
    parity: str = "N",
    stop: int = 1,
    flow: bool = False,
) -> str:
    return f"{port} {baud} {bits}{parity}{stop} flow={flow}"


print(uart_open("/dev/ttyUSB0", baud=9600, flow=True))
print(uart_open("COM3", stop=2, baud=57600))  # order of named arguments does not matter


def pair(first: int, second: int) -> int:
    return first - second


bad_calls: list[Callable[[], object]] = [
    lambda: uart_open("COM3", 9600),  # type: ignore[call-arg]
    lambda: uart_open("COM3", speed=9600),  # type: ignore[call-arg]
    lambda: pair(1, first=2),  # type: ignore[call-arg, misc]
]
for bad in bad_calls:
    try:
        bad()
    except TypeError as exc:
        print(type(exc).__name__, "->", exc)


# ---- positional-only parameters: everything before / cannot be named ----
def clamp(value: float, low: float, high: float, /) -> float:
    return max(low, min(high, value))


print(clamp(105.0, 0.0, 100.0))


# ---- the three kinds in one signature ----
def send(dest: int, payload: bytes, /, retries: int = 3, *, timeout_s: float = 1.0) -> str:
    return f"to {dest:#04x}: {len(payload)} bytes, retries={retries}, timeout={timeout_s} s"


print(send(0x20, b"\x01\x02", 5, timeout_s=0.25))
print(send(0x20, b"\x01\x02", retries=5))


# ---- *args and **kwargs collect extra arguments, and * and ** unpack them at a call ----
def log_event(name: str, *values: int, **fields: str) -> str:
    return f"{name} values={values} fields={sorted(fields.items())}"


port_cfg = {"baud": 38400, "parity": "E"}
print(log_event("boot", 1, 2, 3, board="rev2", fw="1.10.0"))
print(uart_open("COM4", **port_cfg))  # type: ignore[arg-type]
print(send(*(0x21, b"\x00")))

# ---- the standard library is full of keyword-only options ----
rates = [("a", 9600), ("b", 115200), ("c", 57600)]
print(sorted(rates, key=lambda item: item[1], reverse=True))
print(int("ff", base=16), round(3.14159, ndigits=2), max([], default=-1))
print("a", "b", "c", sep="-", end="!\n")
done = subprocess.run(
    [sys.executable, "-c", "print('ok')"], capture_output=True, text=True, check=True, timeout=10
)
print(done.stdout.strip(), done.returncode)


# ---- dataclasses: keyword-only fields and partial() fix named values for later ----
@dataclass(kw_only=True)
class Limits:
    low: float
    high: float
    unit: str = "V"


print(Limits(high=3.45, low=3.15))
open_fast = partial(uart_open, baud=921600, flow=True)
print(open_fast("COM7"), open_fast("COM8", flow=False))


# ---- default values are evaluated once, when def runs ----
def append_bad(item: int, bucket: list[int] = []) -> list[int]:  # noqa: B006
    bucket.append(item)
    return bucket


def append_good(item: int, bucket: list[int] | None = None) -> list[int]:
    if bucket is None:
        bucket = []
    bucket.append(item)
    return bucket


print(append_bad(1), append_bad(2), append_good(1), append_good(2))
