"""Passing options through with **kwargs. Run: python3 kwargs_forwarding.py"""

import functools
import inspect
import subprocess
import sys
from collections.abc import Callable
from typing import Any, NotRequired, TypedDict, Unpack


# ---- 1. A wrapper forwards **kwargs to a function with a known signature ----
def run_tool(cmd: list[str], **kwargs: Any) -> str:
    options = {"timeout": 10, "check": True, "capture_output": True, "text": True} | kwargs
    return str(subprocess.run(cmd, **options).stdout).strip()


print(run_tool([sys.executable, "-c", "print('ok')"]))
try:
    run_tool([sys.executable, "-c", "import time; time.sleep(2)"], timeout=0.2)
except subprocess.TimeoutExpired as exc:
    print("override worked:", type(exc).__name__)
try:
    run_tool([sys.executable, "-c", "pass"], timout=0.2)  # typo, forwarded to Popen
except TypeError as exc:
    print("typo caught:", exc)


# ---- 2. **kwargs that reads its own options hides a typo; named parameters do not ----
def settings_loose(**kwargs: float) -> float:
    return kwargs.get("timeout", 10.0)


def settings_strict(*, timeout: float = 10.0) -> float:
    return timeout


print("loose:", settings_loose(timout=0.2))  # the typo is ignored, the default wins
try:
    settings_strict(timout=0.2)  # type: ignore[call-arg]
except TypeError as exc:
    print("strict:", exc)


# ---- 3. Take what you know, then reject what is left ----
def open_link(port: str, **options: Any) -> str:
    baud = options.pop("baud", 115200)
    timeout = options.pop("timeout", 1.0)
    if options:
        raise TypeError(f"open_link() got unexpected options: {', '.join(sorted(options))}")
    return f"{port} baud={baud} timeout={timeout}"


print(open_link("COM3", baud=9600))
try:
    open_link("COM3", bud=9600, timout=2)
except TypeError as exc:
    print(exc)


# ---- 4. Typed options: the checker knows the names, the run time does not ----
class LinkOptions(TypedDict):
    baud: NotRequired[int]
    timeout: NotRequired[float]


def open_typed(port: str, **options: Unpack[LinkOptions]) -> str:
    return f"{port} baud={options.get('baud', 115200)} timeout={options.get('timeout', 1.0)}"


print(open_typed("COM3", baud=9600))
cfg: LinkOptions = {"baud": 57600, "timeout": 0.5}
print(open_typed("COM4", **cfg))
try:
    open_typed("COM3", **cfg, baud=9600)  # type: ignore[misc]
except TypeError as exc:
    print(exc)


# ---- 5. A decorator passes everything through and keeps the signature ----
def retry[**P, R](times: int) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorate(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for attempt in range(1, times):
                try:
                    return func(*args, **kwargs)
                except OSError:
                    print(f"attempt {attempt} failed")
            return func(*args, **kwargs)

        return wrapper

    return decorate


calls = {"n": 0}


@retry(3)
def read_register(addr: int, *, scale: float = 1.0) -> float:
    calls["n"] += 1
    if calls["n"] < 3:
        raise OSError("bus busy")
    return addr * scale


print(read_register(0x20, scale=0.5))
print(read_register.__name__, inspect.signature(read_register))
