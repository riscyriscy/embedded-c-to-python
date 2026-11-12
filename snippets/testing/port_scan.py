"""List the serial ports, then read one line from the first. Run: uv run port_scan.py"""

import serial
import serial.tools.list_ports


def first_line(device: str) -> str:
    with serial.Serial(device, 115200, timeout=1.0) as port:
        return port.readline().decode("ascii", "replace")


def main() -> None:
    ports = serial.tools.list_ports.comports()
    for info in ports:
        print(info.device, info.description)
    if ports:
        print(first_line(ports[0].device))


if __name__ == "__main__":
    main()
