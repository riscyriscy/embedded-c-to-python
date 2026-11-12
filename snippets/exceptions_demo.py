"""Exceptions, mapped from C error codes. Run: python3 exceptions_demo.py"""

from contextlib import suppress
from pathlib import Path


class FrameError(Exception):
    """Base class for everything this module raises on bad input."""


class ShortFrame(FrameError):
    def __init__(self, got: int, need: int) -> None:
        super().__init__(f"frame too short: {got} bytes, need {need}")
        self.got = got
        self.need = need


class BadChecksum(FrameError):
    def __init__(self, expected: int, actual: int) -> None:
        super().__init__(f"checksum {actual:#04x}, expected {expected:#04x}")


class ConfigError(Exception):
    pass


def build_frame(ftype: int, payload: bytes) -> bytes:
    body = bytes([0xA5, ftype, len(payload)]) + payload
    return body + bytes([-sum(body) & 0xFF])  # all bytes sum to 0 modulo 256


def parse_frame(data: bytes) -> tuple[int, bytes]:
    if len(data) < 4:
        raise ShortFrame(len(data), 4)
    if data[0] != 0xA5:
        raise FrameError(f"bad sync byte {data[0]:#04x}")
    need = 4 + data[2]
    if len(data) < need:
        raise ShortFrame(len(data), need)
    expected = -sum(data[: need - 1]) & 0xFF
    if data[need - 1] != expected:
        raise BadChecksum(expected, data[need - 1])
    return data[1], data[3 : need - 1]


# ---- catch the specific class first and the base class last ----
good = build_frame(0x10, b"\x01\x02")
cases = {
    "good": good,
    "short": good[:3],
    "bad sync": b"\x5a" + good[1:],
    "corrupt": good[:-1] + b"\x00",
}
for label, data in cases.items():
    try:
        ftype, payload = parse_frame(data)
    except ShortFrame as exc:
        print(f"{label:9}ShortFrame: got {exc.got} of {exc.need}")
    except FrameError as exc:
        print(f"{label:9}{type(exc).__name__}: {exc}")
    else:  # runs only when nothing was raised
        print(f"{label:9}type={ftype:#04x} payload={payload.hex()}")


# ---- order of try, except, else and finally ----
def order_demo(fail: bool) -> str:
    steps: list[str] = []
    try:
        steps.append("try")
        if fail:
            raise ValueError("boom")
    except ValueError:
        steps.append("except")
    else:
        steps.append("else")
    finally:  # always runs, like a cleanup label every exit path jumps to
        steps.append("finally")
    return " > ".join(steps)


print(order_demo(False), "|", order_demo(True))


# ---- chaining: keep the original error as the cause ----
def read_setting(settings: dict[str, str], key: str) -> int:
    try:
        return int(settings[key], 0)
    except KeyError as exc:
        raise ConfigError(f"missing setting {key!r}") from exc
    except ValueError as exc:
        raise ConfigError(f"setting {key!r} is not a number: {settings[key]!r}") from exc


for key in ("baud", "parity", "gain"):
    try:
        print(key, "=", read_setting({"baud": "115200", "gain": "high"}, key))
    except ConfigError as exc:
        print(f"{exc} (cause: {type(exc.__cause__).__name__})")

# ---- retry on a transient error ----
outcomes: list[Exception | bytes] = [TimeoutError("no reply"), TimeoutError("no reply"), b"OK"]


def read_reply() -> bytes:
    outcome = outcomes.pop(0)
    if isinstance(outcome, Exception):
        raise outcome
    return outcome


for attempt in range(1, 4):
    try:
        reply = read_reply()
    except TimeoutError as exc:
        print(f"attempt {attempt}: {exc}")
        continue
    print(f"attempt {attempt}: got {reply!r}")
    break
else:
    raise ConfigError("device did not answer in 3 attempts")

# ---- the hierarchy matters: OSError covers the file and socket errors ----
print([cls.__name__ for cls in FileNotFoundError.__mro__])
print([cls.__name__ for cls in KeyError.__mro__])
with suppress(FileNotFoundError):  # ignore one specific, expected error
    Path("does-not-exist.tmp").unlink()
try:
    Path("does-not-exist.tmp").read_bytes()
except OSError as exc:  # catches FileNotFoundError, PermissionError, ...
    print(f"OSError subclass {type(exc).__name__}, errno={exc.errno}")
