"""pyserial behaviours that a loop-back test misses, checked on a pseudo-terminal (Linux, macOS).

Each check asserts what it prints, so the script exits with an error if a pyserial release
changes one of them. Nothing here ran on a real UART, an RS-485 adapter or Windows.
Run: python3 serial_edges.py
"""

import contextlib
import os
import pty
import time
from collections.abc import Callable, Iterator

import serial
import serial.rs485


@contextlib.contextmanager
def pty_port(**kwargs: float | bool | None) -> Iterator[tuple[int, serial.Serial]]:
    master, slave = pty.openpty()
    ser = serial.Serial(os.ttyname(slave), 115200, **kwargs)  # type: ignore[arg-type]
    try:
        yield master, ser
    finally:
        ser.close()
        os.close(master)
        os.close(slave)


def timed(call: Callable[[], object]) -> float:
    start = time.monotonic()
    call()
    return time.monotonic() - start


def main() -> None:
    with pty_port(timeout=0.5) as (master, ser):
        os.write(master, b"\x01\x02\x00\x03\x00")
        first, second = ser.read_until(b"\x00"), ser.read_until(b"\x00")
        assert (first, second) == (b"\x01\x02\x00", b"\x03\x00")
        print("read_until(b'\\x00') returns each frame with its delimiter:", first, second)
        os.write(master, b"\x07\x08")
        assert ser.read_until(b"\x00") == b"\x07\x08"
        print("read_until at the timeout returns the partial frame, so check the last byte")
        os.write(master, b"\x01\x02\x03\x00\x04")
        elapsed = timed(ser.readline)
        assert elapsed >= 0.4
        print(f"readline() on binary data waited {elapsed:.2f} s for a newline that never came")

    with pty_port(timeout=1.0, inter_byte_timeout=0.05) as (master, ser):
        os.write(master, b"abc")
        start = time.monotonic()
        data = ser.read(6)
        elapsed = time.monotonic() - start
        assert data == b"abc" and elapsed >= 0.9
        print(f"inter_byte_timeout=0.05 on Linux: a stalled read(6) still took {elapsed:.2f} s")

    with pty_port(timeout=0.1, write_timeout=0.3) as (_, ser):
        start = time.monotonic()
        try:
            ser.write(bytes(4 * 1024 * 1024))  # nobody reads the other side
        except serial.SerialTimeoutException:
            print(
                f"write() into a full buffer raised SerialTimeoutException after "
                f"{time.monotonic() - start:.2f} s"
            )
        else:
            raise AssertionError("expected a write timeout")

    master, slave = pty.openpty()
    name = os.ttyname(slave)
    first_user = serial.Serial(name, exclusive=True)
    try:
        serial.Serial(name, exclusive=True)
    except serial.SerialException as exc:
        print("second open with exclusive=True:", exc)
    with serial.Serial(name) as shared:  # exclusive=None takes no lock on POSIX
        assert shared.is_open
    print("second open without exclusive=True: succeeded (the lock is advisory)")
    try:
        first_user.rs485_mode = serial.rs485.RS485Settings()
    except ValueError as exc:
        print("native RS-485 ioctl on a pty:", exc)
    first_user.close()
    os.close(master)
    os.close(slave)


if __name__ == "__main__":
    main()
