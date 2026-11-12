"""Type annotations: the syntax, and what Python does with it at run time."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Final, Literal, Protocol, TypedDict, cast

BAUD: Final = 115200  # Final: a type checker rejects a second assignment
Mode = Literal["tx", "rx"]  # only these two strings are allowed


class Frame(TypedDict):  # a dict with known keys, for JSON-like data
    addr: int
    payload: bytes


class Sink(Protocol):  # structural type: anything with write() fits
    def write(self, data: bytes) -> int: ...


@dataclass
class Rail:
    name: str
    volts: float = 3.3  # the annotation makes `volts` a dataclass field


def scale(raw: int, *, vref: float = 3.3, bits: int = 12) -> float:
    return raw * vref / (1 << bits)


def first[T](items: list[T]) -> T | None:  # 3.12: generic function, no TypeVar
    return items[0] if items else None


type Handler = Callable[[bytes], None]  # 3.12: type alias statement


def main() -> None:
    count: int  # declares the type; the name does not exist yet
    print("annotation only:", "count" in locals())
    count = 7
    ratio: float = count / 2
    print("Rail annotations:", Rail.__annotations__)
    print("scale annotations:", scale.__annotations__)
    print("Rail fields:", Rail("3V3").volts, Rail.__dataclass_fields__.keys())
    print("first:", first([4, 5]), first([]), "ratio:", ratio)
    # Python does not check any of this when the program runs
    wrong = scale(2048.0, vref=5)  # type: ignore[arg-type]
    print("scale(2048.0, vref=5) gave:", wrong)
    frame: Frame = {"addr": 1, "payload": b"\x01"}
    print("TypedDict is a plain dict:", type(frame).__name__)
    raw = cast("int", "5")  # cast tells the checker, and converts nothing
    print("cast returned:", repr(raw))
    handler: Handler = print
    handler(b"ok")


if __name__ == "__main__":
    main()
