"""python-can: send and receive frames, filter by ID, listen in the background.

Two Bus objects on the "virtual" interface share one in-process channel, so the script
runs without a CAN adapter. For hardware change `interface` and `channel`, for example
interface="socketcan", channel="can0" on Linux. Run: python3 can_demo.py
"""

import struct
import time

import can

ID_TEMP = 0x1A0  # a made-up message: temperature in 0.01 C (int16) and a counter (uint8)
ID_ALARM = 0x0A1  # lower ID means higher priority on the bus


def encode_temp(centi_c: int, counter: int) -> can.Message:
    return can.Message(
        arbitration_id=ID_TEMP, is_extended_id=False, data=struct.pack("<hB", centi_c, counter)
    )


def decode_temp(msg: can.Message) -> tuple[float, int]:
    centi_c, counter = struct.unpack("<hB", msg.data[:3])
    return centi_c / 100, counter


class Collector(can.Listener):
    """Called from the notifier thread for every received frame."""

    def __init__(self) -> None:
        self.frames: list[can.Message] = []

    def on_message_received(self, msg: can.Message) -> None:
        self.frames.append(msg)


def main() -> None:
    with (
        can.Bus(interface="virtual", channel="rig", receive_own_messages=False) as dut,
        can.Bus(interface="virtual", channel="rig") as host,
    ):
        # 1. One frame, blocking receive with a timeout
        dut.send(encode_temp(2845, 7))
        msg = host.recv(timeout=1.0)
        assert msg is not None
        print(
            f"id={msg.arbitration_id:#05x} dlc={msg.dlc} data={msg.data.hex(' ')}", decode_temp(msg)
        )
        print("nothing pending:", host.recv(timeout=0.05))  # None, not an exception

        # 2. Hardware-style acceptance filters: only ID_ALARM (mask 0x7FF = all 11 bits)
        host.set_filters([{"can_id": ID_ALARM, "can_mask": 0x7FF, "extended": False}])
        dut.send(encode_temp(2900, 8))  # dropped by the filter
        dut.send(can.Message(arbitration_id=ID_ALARM, is_extended_id=False, data=b"\x01"))
        msg = host.recv(timeout=1.0)
        assert msg is not None
        print("filtered:", hex(msg.arbitration_id), msg.data.hex())
        host.set_filters(None)

        # 3. A background listener with a Notifier, and a periodic task on the sender
        collector = Collector()
        notifier = can.Notifier(host, [collector])
        task = dut.send_periodic(encode_temp(2850, 0), period=0.01)
        time.sleep(0.15)
        task.stop()
        time.sleep(0.05)
        notifier.stop()
        n = len(collector.frames)
        print(
            "periodic frames received:",
            5 <= n <= 20,
            "all IDs equal:",
            {f.arbitration_id for f in collector.frames} == {ID_TEMP},
        )

        # 4. An extended (29-bit) ID, and the checks that Message(check=True) makes
        dut.send(can.Message(arbitration_id=0x18DAF110, is_extended_id=True, data=bytes(range(8))))
        ext = host.recv(timeout=1.0)
        assert ext is not None
        print(f"{ext.arbitration_id:#x}", ext.is_extended_id, len(ext.data))
        try:
            can.Message(arbitration_id=0x800, is_extended_id=False, check=True)  # needs 12 bits
        except ValueError as exc:
            print("ValueError:", exc)
        try:
            can.Message(data=bytes(9), check=True)  # classic CAN carries at most 8 bytes
        except ValueError as exc:
            print("ValueError:", exc)


if __name__ == "__main__":
    main()
