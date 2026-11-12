"""Stream RTT text into logging: line reassembly, level prefixes, timestamps.

Run: python3 rtt_logging.py
"""

import logging
import sys
import time
from collections.abc import Callable
from typing import Any, Protocol

from pylink.enums import JLinkRTTErrors  # type: ignore[import-untyped]
from pylink.errors import JLinkRTTException  # type: ignore[import-untyped]

log = logging.getLogger("target")
LEVELS = {
    "E": logging.ERROR,
    "W": logging.WARNING,
    "I": logging.INFO,
    "D": logging.DEBUG,
}


class RttSource(Protocol):
    def read(self, max_bytes: int) -> bytes: ...  # b"" when nothing is waiting


class LineAssembler:
    """Turn chunks that end anywhere into complete lines; keep the unfinished tail."""

    def __init__(self, max_line: int = 256) -> None:
        self._tail = b""
        self._max_line = max_line

    def feed(self, chunk: bytes) -> list[str]:
        *lines, self._tail = (self._tail + chunk).split(b"\n")
        if len(self._tail) >= self._max_line:  # a line that never ends
            lines.append(self.flush())
        return [decode(line) for line in lines]

    def flush(self) -> bytes:
        tail, self._tail = self._tail, b""
        return tail


def decode(line: bytes) -> str:  # whole lines only: UTF-8 can be split
    return line.rstrip(b"\r").decode("utf-8", errors="replace")


def parse_level(line: str) -> tuple[int, str]:
    """'E: sensor timeout' gives (logging.ERROR, 'sensor timeout'); else INFO."""
    if line[1:2] == ":" and line[:1] in LEVELS:
        return LEVELS[line[:1]], line[2:].lstrip()
    return logging.INFO, line


def emit(lines: list[str], stamp: float) -> None:
    for line in lines:
        level, text = parse_level(line)
        log.log(level, text, extra={"t": stamp})


def pump(
    source: RttSource,
    stop: Callable[[], bool],
    poll_s: float = 0.05,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> int:
    """Log every line from source until stop() is true. Returns the line count."""
    assembler, count = LineAssembler(), 0
    while not stop():
        chunk = source.read(1024)
        if not chunk:
            sleep(poll_s)
            continue
        lines = assembler.feed(chunk)
        emit(lines, clock())  # RTT carries no time: this is when the host read it
        count += len(lines)
    if tail := assembler.flush():  # a last line without a newline
        emit([decode(tail)], clock())
        count += 1
    return count


class PyLinkRtt:
    """RttSource over pylink: `jlink` is an open, connected pylink.JLink."""

    def __init__(self, jlink: Any, buffer_index: int = 0) -> None:
        self._jlink, self._index = jlink, buffer_index

    def start(
        self,
        timeout_s: float = 5.0,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> int:
        """Start RTT and wait for the control block. Returns the up-buffer count."""
        self._jlink.rtt_start()
        deadline = clock() + timeout_s
        while True:
            try:
                return int(self._jlink.rtt_get_num_up_buffers())
            except JLinkRTTException:  # control block not found yet
                if clock() > deadline:
                    raise TimeoutError("RTT control block not found") from None
                sleep(0.1)

    def read(self, max_bytes: int) -> bytes:
        return bytes(self._jlink.rtt_read(self._index, max_bytes))


class StandInJLink:
    """Same methods as pylink.JLink; delivers scripted chunks of target output."""

    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks, self._probes = chunks, 2

    def rtt_start(self) -> None:
        pass

    def rtt_get_num_up_buffers(self) -> int:
        if self._probes:  # the firmware has not set up its control block yet
            self._probes -= 1
            raise JLinkRTTException(JLinkRTTErrors.RTT_ERROR_CONTROL_BLOCK_NOT_FOUND)
        return 3

    def rtt_read(self, buffer_index: int, num_bytes: int) -> list[int]:
        return list(self._chunks.pop(0)[:num_bytes]) if self._chunks else []

    @property
    def done(self) -> bool:
        return not self._chunks


def main() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(t)7.2f %(levelname)-7s %(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)
    ticks = iter(range(1, 100))
    jlink = StandInJLink(
        [
            b"I: boot ok\nW: low vol",  # the first line arrives in two pieces
            b"tage 3.1\r\nE: sensor",
            b" timeout\nD: tick\n",
            b"I: temp 25 \xc2",  # a UTF-8 character split between reads
            b"\xb0C\nplain text\nI: shut",
        ]
    )
    rtt = PyLinkRtt(jlink)
    print("up buffers:", rtt.start(sleep=lambda s: None))
    lines = pump(rtt, lambda: jlink.done, clock=lambda: next(ticks) * 0.25)
    print("lines logged:", lines)


if __name__ == "__main__":
    main()
