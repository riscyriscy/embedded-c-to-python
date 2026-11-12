"""pyusb: find a device, read a bulk IN endpoint, send a control request.

No USB device is needed: the parsing code runs against a FakeDevice that has the same
methods as usb.core.Device. The functions find_device() and read_packets() are the ones
to use on hardware. Run: python3 usb_demo.py
"""

import struct
from collections.abc import Iterator
from typing import Any, Protocol

import usb.core  # type: ignore[import-untyped]  # pyusb has no type stubs
import usb.util  # type: ignore[import-untyped]

VID, PID = 0xCAFE, 0x4001  # placeholders: TinyUSB's example vendor ID and a made-up product ID
EP_IN = 0x81  # bit 7 set means device-to-host
PACKET = struct.Struct("<IhhH")  # ms, temperature in 0.01 C, millivolts, flags


class UsbDevice(Protocol):
    """The part of usb.core.Device that this script uses."""

    def set_configuration(self) -> None: ...
    def read(self, endpoint: int, size_or_buffer: int, timeout: int = ...) -> Any: ...
    def ctrl_transfer(
        self,
        bmRequestType: int,
        bRequest: int,
        wValue: int = ...,
        wIndex: int = ...,
        data_or_wLength: int = ...,
    ) -> Any: ...


def find_device(vid: int = VID, pid: int = PID) -> usb.core.Device | None:
    """Return the first matching device, or None. Raises NoBackendError if libusb is missing."""
    return usb.core.find(idVendor=vid, idProduct=pid)


def firmware_version(dev: UsbDevice) -> str:
    # bmRequestType 0xC0 = device-to-host, vendor request, recipient device
    data = bytes(dev.ctrl_transfer(0xC0, 0x01, 0, 0, 3))
    return ".".join(str(b) for b in data)


def read_packets(
    dev: UsbDevice, count: int, timeout_ms: int = 500
) -> Iterator[tuple[int, float, int, int]]:
    dev.set_configuration()  # needed once; on Linux a kernel driver may have to be detached first
    for _ in range(count):
        try:
            raw = bytes(dev.read(EP_IN, PACKET.size, timeout_ms))
        except usb.core.USBTimeoutError:
            return  # no data within the timeout: stop, do not hang
        ms, centi_c, mv, flags = PACKET.unpack(raw)
        yield ms, centi_c / 100, mv, flags


class FakeDevice:
    """Replays packets and answers the version request, with the methods of usb.core.Device."""

    def __init__(self, packets: list[bytes]) -> None:
        self.packets = packets
        self.configured = False

    def set_configuration(self) -> None:
        self.configured = True

    def read(self, endpoint: int, size_or_buffer: int, timeout: int = 0) -> bytes:
        assert endpoint == EP_IN and self.configured
        if not self.packets:
            raise usb.core.USBTimeoutError("Operation timed out", errno=110)
        return self.packets.pop(0)

    def ctrl_transfer(
        self,
        bmRequestType: int,
        bRequest: int,
        wValue: int = 0,
        wIndex: int = 0,
        data_or_wLength: int = 0,
    ) -> bytes:
        return bytes([1, 10, 0]) if (bmRequestType, bRequest) == (0xC0, 0x01) else b""


def main() -> None:
    print("device present:", find_device() is not None)  # False unless your device is attached
    fake = FakeDevice([PACKET.pack(1000 * i, 2800 + 15 * i, 3300 - i, 1 << i) for i in range(3)])
    print("firmware", firmware_version(fake))
    for packet in read_packets(fake, count=5):  # 5 requested, 3 available: the timeout ends it
        print(packet)

    # Walking the descriptors of a real device (needs hardware):
    #   for cfg in dev:
    #       for intf in cfg:
    #           for ep in intf:
    #               print(hex(ep.bEndpointAddress), usb.util.endpoint_type(ep.bmAttributes))
    print(
        usb.util.endpoint_direction(EP_IN) == usb.util.ENDPOINT_IN,
        usb.util.endpoint_direction(0x01),
    )


if __name__ == "__main__":
    main()
