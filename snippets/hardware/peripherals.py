"""I2C, SPI, GPIO edge and memory-mapped registers from Python, each behind a Protocol with a fake."""

from __future__ import annotations

import ctypes
import mmap
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Protocol

TEMP_ADDR = 0x48  # a 16-bit temperature sensor: register 0x00 is the temperature, 0x0F the device ID
LSB_C = 0.0078125  # degrees C per count


class I2cBus(Protocol):
    def read_i2c_block_data(self, i2c_addr: int, register: int, length: int, force: bool | None = None) -> list[int]: ...


class FakeI2c:
    def __init__(self, registers: dict[int, int]) -> None:
        self.registers = registers  # register -> 16-bit value

    def read_i2c_block_data(self, i2c_addr: int, register: int, length: int, force: bool | None = None) -> list[int]:
        if i2c_addr != TEMP_ADDR:
            raise OSError(121, "Remote I/O error")  # what a missing device gives on Linux
        return list(self.registers[register].to_bytes(2, "big"))[:length]


def read_temperature(bus: I2cBus, addr: int = TEMP_ADDR) -> float:
    raw = int.from_bytes(bytes(bus.read_i2c_block_data(addr, 0x00, 2)), "big", signed=True)
    return raw * LSB_C


class SpiPort(Protocol):
    def xfer2(self, values: list[int]) -> list[int]: ...


class FakeSpiFlash:
    """Answers the JEDEC ID command (0x9F) as a 25-series serial flash does."""

    def xfer2(self, values: list[int]) -> list[int]:
        if values[0] == 0x9F:
            return [0, 0xEF, 0x40, 0x18][: len(values)]
        return [0] * len(values)


def jedec_id(spi: SpiPort) -> str:
    reply = spi.xfer2([0x9F, 0, 0, 0])  # one transfer: the command out, three bytes back
    return " ".join(f"{b:02X}" for b in reply[1:4])


class EdgeInput(Protocol):
    def wait_edge(self, timeout_s: float) -> bool: ...


class FakeEdge:
    def __init__(self) -> None:
        self._event = threading.Event()

    def trigger(self) -> None:
        self._event.set()

    def wait_edge(self, timeout_s: float) -> bool:
        hit = self._event.wait(timeout_s)
        self._event.clear()
        return hit


class GpiodInput:
    """The same Protocol on real hardware, with libgpiod 2.x (gpiod 2.5.0): not used by the host run below."""

    def __init__(self, chip: str, line: int) -> None:
        import gpiod
        from gpiod.line import Direction, Edge

        settings = gpiod.LineSettings(direction=Direction.INPUT, edge_detection=Edge.RISING)
        self._request = gpiod.request_lines(chip, consumer="rig", config={line: settings})

    def wait_edge(self, timeout_s: float) -> bool:
        if not self._request.wait_edge_events(timeout_s):
            return False
        self._request.read_edge_events()  # drain, so the next wait sees only a new edge
        return True


class Regs(ctypes.Structure):
    _fields_ = [("ID", ctypes.c_uint32), ("CTRL", ctypes.c_uint32), ("STATUS", ctypes.c_uint32), ("DATA", ctypes.c_uint32)]


ENABLE, READY = 1 << 0, 1 << 1


def enable_and_wait(words: memoryview, timeout_s: float) -> bool:
    words[1] |= ENABLE  # read-modify-write of CTRL, word index 1
    deadline = time.monotonic() + timeout_s
    while not words[2] & READY:  # poll STATUS, word index 2, with a timeout
        if time.monotonic() > deadline:
            return False
        time.sleep(0.001)
    return True


def main() -> None:
    print("I2C temperature:", read_temperature(FakeI2c({0x00: 0x0C80, 0x0F: 0x0117})), "C")
    print("raw 0xFF00 as signed:", read_temperature(FakeI2c({0x00: 0xFF00})), "C")
    try:
        read_temperature(FakeI2c({}), addr=0x49)
    except OSError as exc:
        print("missing device:", exc)
    print("SPI JEDEC ID:", jedec_id(FakeSpiFlash()))
    edge = FakeEdge()
    start = time.monotonic()
    print("edge with no trigger:", edge.wait_edge(0.2), "after %.1f s" % (time.monotonic() - start))
    threading.Timer(0.05, edge.trigger).start()
    print("edge triggered by a timer:", edge.wait_edge(1.0))

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "regs.bin"  # stands in for /dev/uio0
        path.write_bytes((0x5A5A0001).to_bytes(4, "little") + bytes(4096 - 4))
        fd = os.open(path, os.O_RDWR)
        with mmap.mmap(fd, 4096) as page:
            regs = Regs.from_buffer(page)
            words = memoryview(page).cast("I")
            print("offsets:", {name: getattr(Regs, name).offset for name in ("ID", "CTRL", "STATUS", "DATA")})
            print(f"ID register: {regs.ID:#010x}")
            print("ready never set:", enable_and_wait(words, 0.05), f"CTRL = {regs.CTRL:#x}")
            threading.Timer(0.02, lambda: words.__setitem__(2, READY)).start()  # the 'device' answers
            print("ready after 20 ms:", enable_and_wait(words, 0.5))
            words.release()
            del regs
        os.close(fd)


if __name__ == "__main__":
    main()
