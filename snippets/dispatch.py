"""Message decoding with a class hierarchy and a dispatch table. Run: python3 dispatch.py"""

from __future__ import annotations

import struct
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, ClassVar, Self

LEVELS = ["DBG", "INF", "WRN", "ERR"]


class Message(ABC):
    """Base class for every message type. Subclasses register themselves by TYPE."""

    TYPE: ClassVar[int]
    _registry: ClassVar[dict[int, type[Message]]] = {}

    def __init_subclass__(cls, **kwargs: object) -> None:  # runs once per subclass definition
        super().__init_subclass__(**kwargs)
        if cls.TYPE in Message._registry:
            raise TypeError(f"duplicate message type {cls.TYPE:#04x}")
        Message._registry[cls.TYPE] = cls

    @classmethod
    @abstractmethod
    def from_payload(cls, payload: bytes) -> Self: ...

    @staticmethod
    def decode(msg_type: int, payload: bytes) -> Message | None:
        cls = Message._registry.get(msg_type)  # like indexing a table of constructors in C
        return cls.from_payload(payload) if cls else None


@dataclass(frozen=True)
class Ping(Message):
    TYPE: ClassVar[int] = 0x01
    token: int

    @classmethod
    def from_payload(cls, payload: bytes) -> Self:
        (token,) = struct.unpack("<I", payload)
        return cls(token)


@dataclass(frozen=True)
class SetRate(Message):
    TYPE: ClassVar[int] = 0x20
    period_ms: int

    def __post_init__(self) -> None:  # runs for every SetRate, however it was built
        if not 10 <= self.period_ms <= 10_000:
            raise ValueError(f"period {self.period_ms} ms out of range")

    @classmethod
    def from_payload(cls, payload: bytes) -> Self:
        (period,) = struct.unpack("<H", payload)
        return cls(period)


@dataclass(frozen=True)
class Log(Message):
    TYPE: ClassVar[int] = 0x30
    level: int
    text: str

    def __post_init__(self) -> None:
        if not 0 <= self.level < len(LEVELS):
            raise ValueError(f"log level {self.level} out of range")

    @classmethod
    def from_payload(cls, payload: bytes) -> Self:
        if not payload:
            raise ValueError("log payload has no level byte")
        return cls(payload[0], payload[1:].decode("ascii", errors="replace"))


def on_ping(m: Ping) -> str:
    return f"pong to token {m.token:#x}"


def on_set_rate(m: SetRate) -> str:
    return f"rate set to {m.period_ms} ms"


# Handlers in a dict keyed by class: the Python form of a C function-pointer table
handlers: dict[type[Message], Callable[[Any], str]] = {Ping: on_ping, SetRate: on_set_rate}


def handle(m: Message) -> str:
    # Structural pattern matching on classes is the other common choice
    match m:
        case Log(level=lvl, text=text) if lvl >= 2:
            return f"device {LEVELS[lvl]}: {text}"
        case Log():
            return "(log below warning level ignored)"
        case _:
            return handlers[type(m)](m)


incoming = [
    (0x01, struct.pack("<I", 0xC0FFEE)),
    (0x20, struct.pack("<H", 250)),
    (0x30, bytes([3]) + b"brown-out reset"),
    (0x30, bytes([0]) + b"tick"),
    (0x7E, b""),
    (0x20, struct.pack("<H", 5)),
    (0x30, b""),  # malformed: Log with no level byte
    (0x30, bytes([7]) + b"bad level"),  # malformed: level outside LEVELS
]
for msg_type, payload in incoming:
    try:  # wire data is untrusted: decoding and handling both sit inside the try
        msg = Message.decode(msg_type, payload)
        result = handle(msg) if msg else "unknown type, skipped"
    except (ValueError, struct.error) as e:  # a missing handler is a bug: KeyError is not caught
        print(f"{msg_type:#04x}: rejected ({e})")
        continue
    print(f"{msg_type:#04x}: {result}")
print("registered:", {f"{t:#04x}": c.__name__ for t, c in Message._registry.items()})
