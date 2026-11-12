from typing import NotRequired, TypedDict, Unpack


class LinkOptions(TypedDict):
    baud: NotRequired[int]
    timeout: NotRequired[float]


def open_typed(port: str, **options: Unpack[LinkOptions]) -> str:
    return f"{port} {options}"


open_typed("COM3", bud=9600)
open_typed("COM3", baud="fast")
