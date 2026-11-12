"""pyserial: open a port, send SCPI-style commands, handle timeouts and errors.

The device is simulated with a pseudo-terminal (Linux and macOS), so the script runs
without hardware. Replace `port` with "/dev/ttyUSB0" or "COM3" for a real instrument.
Run: python3 serial_demo.py
"""

import contextlib
import os
import pty
import threading
from types import TracebackType
from typing import Self

import serial
import serial.tools.list_ports

try:
    from termios import error as _termios_error  # POSIX only

    TTY_ERRORS: tuple[type[Exception], ...] = (_termios_error,)
except ImportError:  # Windows has no termios
    TTY_ERRORS = ()

RAW_ERRORS: tuple[type[Exception], ...] = (OSError, *TTY_ERRORS)

REPLIES = {b"*IDN?": b"TLM-100,SN0007,1.10.0", b"TEMP?": b"28.4", b"RATE 250": b"OK"}
RELEASE_LATE = threading.Event()  # lets the "LATE" reply go out, so the demo needs no fixed delay


def fake_device(master_fd: int) -> None:
    """Answer one line at a time, like an instrument. Unknown commands get ERR."""
    buf = b""
    while True:
        try:
            chunk = os.read(master_fd, 64)
        except OSError:  # the other side closed
            return
        buf += chunk
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            if line.strip() == b"SILENT":  # a device that does not answer
                continue
            if line.strip() == b"LATE":  # a slow device: it answers only after RELEASE_LATE is set
                RELEASE_LATE.wait(5.0)
                os.write(master_fd, b"LATE-REPLY\r\n")
                continue
            os.write(master_fd, REPLIES.get(line.strip(), b"ERR 1") + b"\r\n")


class SerialTransport:
    """Request and reply over a serial port: query(command) returns the reply line."""

    def __init__(self, port: str, baudrate: int = 115200, timeout_s: float = 0.5) -> None:
        # timeout is the maximum wait for a read, so a dead device cannot hang the script
        self.ser = serial.Serial(port, baudrate=baudrate, timeout=timeout_s, write_timeout=1.0)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        self.ser.close()

    def query(self, command: str) -> str:
        try:
            # Drops only the bytes that have already arrived. A reply that arrives after this
            # call (a slow device, after a timeout) is not dropped and answers the next query.
            self.ser.reset_input_buffer()
            self.ser.write(command.encode("ascii") + b"\n")
            reply = self.ser.readline()  # returns when "\n" arrives or the timeout expires
        except TTY_ERRORS as exc:
            # On Linux, reset_input_buffer() on an unplugged adapter raises termios.error,
            # which is not an OSError. Convert it so callers see one "link gone" type.
            raise serial.SerialException(f"port lost: {exc}") from exc
        if not reply.endswith(b"\n"):
            raise TimeoutError(f"no reply to {command!r}")
        return reply.decode("ascii").strip()


def main() -> None:
    ports = serial.tools.list_ports.comports()
    print("comports() returns a list:", isinstance(ports, list))  # contents depend on the machine

    master_fd, slave_fd = pty.openpty()
    port = os.ttyname(slave_fd)
    threading.Thread(target=fake_device, args=(master_fd,), daemon=True).start()

    with SerialTransport(port) as link:
        print(link.query("*IDN?"))
        print(float(link.query("TEMP?")) + 0.1, link.query("RATE 250"), link.query("BOGUS"))
        s = link.ser
        print(s.baudrate, s.bytesize, s.parity, s.stopbits, s.timeout, s.is_open)
        s.timeout = 0.1  # a read with nothing to read returns b"" after the timeout
        print(s.read(4), s.in_waiting)
        try:
            link.query("SILENT")
        except TimeoutError as exc:
            print("TimeoutError:", exc)
        s.close()
        try:
            s.write(b"x")  # writing to a closed port
        except serial.PortNotOpenError as exc:
            print("PortNotOpenError:", exc)

    # A port that does not exist raises SerialException at construction
    try:
        serial.Serial("/dev/does-not-exist")
    except serial.SerialException as exc:
        print("SerialException:", type(exc).__name__, "ok")

    # An unplugged adapter: closing the master side of a pty has the same effect on Linux
    unplugged_master, unplugged_slave = pty.openpty()
    with SerialTransport(os.ttyname(unplugged_slave)) as gone:
        os.close(unplugged_master)
        try:
            gone.ser.reset_input_buffer()  # the raw pyserial call
        except RAW_ERRORS as exc:
            print(
                "raw reset_input_buffer:",
                f"{type(exc).__module__}.{type(exc).__name__}",
                "is an OSError:",
                isinstance(exc, OSError),
            )
        try:
            gone.query("*IDN?")
        except OSError as exc:
            print("query:", type(exc).__name__, "is an OSError:", isinstance(exc, OSError))
    os.close(unplugged_slave)

    # loop:// echoes what is written, which makes unit tests possible with no device and no pty
    with serial.serial_for_url("loop://", timeout=0.2) as loop:
        loop.write(b"\xa5\x10\x02\x00\x01\x02")
        print(loop.read(6).hex(" "), loop.read(1))

    # A late reply to a timed-out query arrives after reset_input_buffer() and is taken as the
    # answer to the next query. The real answer to that query stays in the buffer.
    with SerialTransport(port, timeout_s=0.1) as late:
        with contextlib.suppress(TimeoutError):
            late.query("LATE")
        late.ser.timeout = 0.5
        threading.Timer(0.1, RELEASE_LATE.set).start()  # the reply comes in during query 2
        first = late.query("TEMP?")
        print(
            "late reply: query('TEMP?') returned", repr(first), "| next line:", late.ser.readline()
        )
    os.close(slave_fd)
    os.close(master_fd)


if __name__ == "__main__":
    main()
