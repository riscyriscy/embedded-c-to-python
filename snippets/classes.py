"""Classes for firmware engineers: registers, versions, drivers, rigs. Run: python3 classes.py"""

from __future__ import annotations

import enum
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Protocol, Self


# ---- A small class with validation, a property and a readable repr ----
@dataclass(frozen=True, slots=True)
class Field:
    """One bit field inside a register."""

    name: str
    lsb: int
    width: int = 1

    def __post_init__(self) -> None:  # runs after the generated __init__: validate once
        if not 0 <= self.lsb < 32 or not 1 <= self.width <= 32 - self.lsb:
            raise ValueError(f"field {self.name} does not fit in 32 bits")

    @property
    def mask(self) -> int:  # computed on access, read like an attribute
        return ((1 << self.width) - 1) << self.lsb


class Register:
    """A 32-bit register value with named fields: the Python version of a bitfield struct."""

    def __init__(self, name: str, fields: list[Field], value: int = 0) -> None:
        self.name = name
        self._fields = {f.name: f for f in fields}  # leading underscore: internal by convention
        self.value = value

    def __getitem__(self, name: str) -> int:  # reg["MODE"]
        f = self._fields[name]
        return (self.value & f.mask) >> f.lsb

    def __setitem__(self, name: str, v: int) -> None:  # reg["MODE"] = 2
        f = self._fields[name]
        if not 0 <= v < (1 << f.width):
            raise ValueError(f"{self.name}.{name}: {v} does not fit in {f.width} bit(s)")
        self.value = (self.value & ~f.mask) | (v << f.lsb)

    def __repr__(self) -> str:
        decoded = ", ".join(f"{n}={self[n]}" for n in self._fields)
        return f"{self.name}({self.value:#010x}: {decoded})"


CTRL_FIELDS = [Field("EN", 0), Field("MODE", 1, 2), Field("DIV", 8, 4), Field("IRQ", 31)]
ctrl = Register("CTRL", CTRL_FIELDS)
ctrl["EN"] = 1
ctrl["MODE"] = 2
ctrl["DIV"] = 9
print(ctrl)
try:
    ctrl["MODE"] = 4
except ValueError as e:
    print(f"rejected: {e}")
print(f"decode a value read from hardware: {Register('CTRL', CTRL_FIELDS, 0x80000301)}")


# ---- order=True: comparison operators generated from the fields, in order ----
@dataclass(frozen=True, order=True)
class FirmwareVersion:
    major: int
    minor: int
    patch: int = 0

    @classmethod
    def parse(cls, text: str) -> Self:  # alternative constructor
        major, minor, patch = (int(p) for p in text.removeprefix("v").split("."))
        return cls(major, minor, patch)

    def __str__(self) -> str:  # str() / print(); __repr__ stays the generated one
        return f"v{self.major}.{self.minor}.{self.patch}"


fleet = [FirmwareVersion.parse(t) for t in ["v1.10.0", "v1.9.3", "v2.0.1", "v1.10.0"]]
print(f"newest: {max(fleet)}")
print(f"unique, sorted: {[str(v) for v in sorted(set(fleet))]}")  # frozen dataclass: hashable
print(f"below v2.0: {[str(v) for v in fleet if v < FirmwareVersion(2, 0)]}")
print(f"repr for debugging: {fleet[0]!r}")


# ---- Enum with data and behaviour: supply rails and their tolerances ----
class Rail(enum.Enum):
    V3V3 = (3.3, 0.05)
    V1V8 = (1.8, 0.03)
    V0V9 = (0.9, 0.03)

    def __init__(self, nominal: float, tolerance: float) -> None:
        self.nominal = nominal
        self.tolerance = tolerance

    def check(self, measured: float) -> bool:
        return abs(measured - self.nominal) <= self.nominal * self.tolerance


readings = {Rail.V3V3: 3.31, Rail.V1V8: 1.71, Rail.V0V9: 0.91}
print("rails:", {r.name: ("PASS" if r.check(v) else "FAIL") for r, v in readings.items()})


# ---- Protocol: an interface by shape (duck typing), checked by mypy ----
class Transport(Protocol):
    def write(self, data: bytes) -> None: ...
    def read_line(self) -> bytes: ...


@dataclass
class FakeTransport:
    """Scripted stand-in for a serial port: records writes, replays canned replies."""

    replies: list[bytes]
    sent: list[bytes] = field(default_factory=list)  # never use a bare [] default

    def write(self, data: bytes) -> None:
        self.sent.append(data)

    def read_line(self) -> bytes:
        return self.replies.pop(0)


class TempSensor:
    """Driver class: composition (has a Transport) rather than inheritance."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def read_celsius(self) -> float:
        self._t.write(b"TEMP?\n")
        reply = self._t.read_line().strip()  # e.g. b"T=2534" in centi-degrees
        if not reply.startswith(b"T="):
            raise OSError(f"unexpected reply {reply!r}")
        return int(reply[2:]) / 100


fake = FakeTransport(replies=[b"T=2534\n", b"ERR\n"])
sensor = TempSensor(fake)
print(f"temperature {sensor.read_celsius()} C, sent {fake.sent}")
try:
    sensor.read_celsius()
except OSError as e:
    print(f"driver error: {e}")


# ---- Context manager class: a bench supply that is always switched off ----
class BenchSupply:
    def __init__(self, volts: float) -> None:
        self.volts = volts
        self.log: list[str] = []

    def __enter__(self) -> Self:
        self.log += [f"VOLT {self.volts}", "OUTP ON"]
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.log.append("OUTP OFF")  # runs on success, exception or Ctrl+C


psu = BenchSupply(12.0)
try:
    with psu:
        raise RuntimeError("DUT did not boot")
except RuntimeError:
    pass
print(f"SCPI sent even though the test failed: {psu.log}")


# ---- Iterable class: a test-point sweep usable in for loops and comprehensions ----
@dataclass(frozen=True)
class Sweep:
    start: float
    stop: float
    steps: int

    def __iter__(self) -> Iterator[float]:  # a generator method makes the class iterable
        for i in range(self.steps):
            yield self.start + (self.stop - self.start) * i / (self.steps - 1)

    def __len__(self) -> int:
        return self.steps


sweep = Sweep(3.0, 3.6, 4)
print(f"{len(sweep)} test points: {[round(v, 2) for v in sweep]}")
