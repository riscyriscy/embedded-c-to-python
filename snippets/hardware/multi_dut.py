"""Choose serial ports by serial number or USB location, and run one worker per DUT.

The three adapters are ListPortInfo objects built by hand, so that the selection logic runs on a
machine with no adapters. The three DUTs are simulated on pseudo-terminals (Linux and macOS).
Run: python3 multi_dut.py
"""

import os
import pty
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from statistics import mean

import serial
from serial.tools.list_ports_common import ListPortInfo


class PortError(Exception):
    pass


def adapter(
    device: str, vid: int, pid: int, serial_number: str | None, location: str
) -> ListPortInfo:
    info = ListPortInfo(device, skip_link_detection=True)
    info.vid, info.pid, info.serial_number, info.location = vid, pid, serial_number, location
    return info


def pick_port(
    ports: list[ListPortInfo],
    vid: int,
    pid: int,
    serial_number: str | None = None,
    location: str | None = None,
) -> str:
    """The one port that matches every given field, or a PortError that says what was found."""
    found = [
        p
        for p in ports
        if (p.vid, p.pid) == (vid, pid)
        and (serial_number is None or p.serial_number == serial_number)
        and (location is None or p.location == location)
    ]
    if len(found) != 1:
        names = ", ".join(
            f"{p.device} ({p.serial_number or 'no serial'}, {p.location})" for p in found
        )
        raise PortError(f"{len(found)} ports match" + (f": {names}" if found else ""))
    return found[0].device


def simulated_dut(serial_number: str, base_c: float, delay_s: float) -> str:
    """A DUT on a pseudo-terminal. Returns the name of the port that the host side opens."""
    master, slave = pty.openpty()

    def serve() -> None:
        buf = b""
        while True:
            try:
                buf += os.read(master, 64)
            except OSError:
                return
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                time.sleep(delay_s)  # the time the firmware takes to answer
                reply = {
                    b"*IDN?": f"TLM-100,{serial_number}".encode(),
                    b"TEMP?": f"{base_c}".encode(),
                }
                os.write(master, reply.get(line.strip(), b"ERR 1") + b"\r\n")

    threading.Thread(target=serve, daemon=True).start()
    return os.ttyname(slave)


def test_dut(port: str) -> str:
    with serial.Serial(port, 115200, timeout=1.0, write_timeout=1.0) as ser:

        def ask(command: str) -> str:
            ser.write(command.encode() + b"\n")
            return ser.readline().decode().strip()

        ident = ask("*IDN?").split(",")[1]
        temps = [float(ask("TEMP?")) for _ in range(5)]
    return f"{ident}: 5 readings, mean {mean(temps):.1f} C"


def main() -> None:
    ports = [
        adapter("/dev/ttyUSB0", 0x0403, 0x6001, "A50285BI", "1-2.1"),
        adapter("/dev/ttyUSB1", 0x0403, 0x6001, "A50285BJ", "1-2.2"),
        adapter("/dev/ttyUSB2", 0x0403, 0x6001, None, "1-2.3"),  # a clone with no serial number
    ]
    attempts: list[tuple[int, int, str | None, str | None]] = [
        (0x0403, 0x6001, None, None),
        (0x0403, 0x6001, "A50285BJ", None),
        (0x0403, 0x6001, None, "1-2.3"),
        (0x10C4, 0xEA60, None, None),
    ]
    for vid, pid, serial_number, location in attempts:
        label = f"{vid:04x}:{pid:04x} serial={serial_number} location={location}"
        try:
            print(f"{label} -> {pick_port(ports, vid, pid, serial_number, location)}")
        except PortError as exc:
            print(f"{label} -> PortError: {exc}")

    duts = [simulated_dut(f"SN000{n}", 25.0 + n, 0.1) for n in (1, 2, 3)]
    start = time.perf_counter()
    for port in duts:
        test_dut(port)
    in_turn = time.perf_counter() - start

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=len(duts)) as pool:
        for line in pool.map(test_dut, duts):  # one worker per DUT, each with its own port
            print(line)
    together = time.perf_counter() - start
    print(f"three DUTs one after the other: {in_turn:.1f} s, one worker per DUT: {together:.1f} s")


if __name__ == "__main__":
    main()
