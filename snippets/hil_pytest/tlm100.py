"""TLM-100 line protocol: a Transport, a simulated device, a pyserial transport.

Run: not run by itself; conftest.py and the tests import it.
"""

import time
from collections import deque
from typing import Protocol

import serial


class Transport(Protocol):
    def write(self, data: bytes) -> None: ...
    def read_line(self) -> bytes: ...
    def close(self) -> None: ...


REPLIES = {"ID?": "TLM-100,TLM100-0007,1.10.0", "TEMP?": "T=2534", "RESET": "OK"}


class FakeDevice:
    """Simulated TLM-100: answers ID? and TEMP?, and RESET, and never answers HANG."""

    def __init__(self) -> None:
        self._out: deque[bytes] = deque()

    def write(self, data: bytes) -> None:
        cmd = data.decode("ascii").strip()
        print(f"fake device got {cmd}")
        if cmd != "HANG":  # a locked-up firmware never answers
            self._out.append(REPLIES.get(cmd, f"ERR {cmd}").encode() + b"\n")

    def read_line(self) -> bytes:
        while not self._out:  # no deadline: waits forever, like a dead link
            time.sleep(0.01)
        return self._out.popleft()

    def close(self) -> None:
        pass


class SerialTransport:
    """The same three methods over a real port (pyserial)."""

    def __init__(self, port: str, baud: int = 115200, timeout: float = 1.0) -> None:
        self._port = serial.serial_for_url(port, baud, timeout=timeout)

    def write(self, data: bytes) -> None:
        self._port.write(data)

    def read_line(self) -> bytes:
        line: bytes = self._port.readline()
        if not line.endswith(b"\n"):
            raise TimeoutError("no complete line from the device")
        return line

    def close(self) -> None:
        self._port.close()


def query(link: Transport, command: str) -> str:
    link.write(command.encode() + b"\n")
    return link.read_line().decode("ascii").strip()


def parse_temp(reply: str) -> float:  # 'T=2534' is 25.34 degrees C
    return int(reply.removeprefix("T=")) / 100
