"""python-can behaviours that matter on a real bus, checked on the virtual interface.

The virtual bus has no bit timing, error frames or bus-off state, so this script checks
only what it can: `bus.state`, `bus.shutdown()` and the bit timing calculator. A SocketCAN
test on `vcan0` and a test on real hardware are separate steps (see the book). Nothing
here used a kernel CAN driver. Run: python3 can_edges.py
"""

import can


def main() -> None:
    bus = can.Bus(interface="virtual", channel="edges")
    assert bus.state is can.BusState.ACTIVE
    print("virtual bus state:", bus.state.name, "(real adapters can also report PASSIVE and ERROR)")
    try:
        bus.state = can.BusState.PASSIVE
    except NotImplementedError:
        print("setting bus.state on the virtual bus: NotImplementedError")
    listener = can.Bus(interface="virtual", channel="edges")
    bus.send_periodic(can.Message(arbitration_id=0x100, data=[1]), 0.01)
    assert listener.recv(timeout=0.5) is not None  # the periodic task is sending
    bus.shutdown()
    while listener.recv(timeout=0.05) is not None:  # drain what was already queued
        pass
    assert listener.recv(timeout=0.1) is None
    listener.shutdown()
    print("after shutdown() the periodic task sends nothing more")
    try:
        bus.send(can.Message(arbitration_id=0x100, data=[1]))
    except can.CanOperationError as exc:
        print("send() after shutdown():", type(exc).__name__, "-", exc)
    bus.shutdown()  # a second call is harmless
    with can.Bus(interface="virtual", channel="edges") as other:
        assert other.state is can.BusState.ACTIVE  # leaving the block calls shutdown()

    timing = can.BitTiming.from_sample_point(f_clock=8_000_000, bitrate=500_000, sample_point=80.0)
    assert timing.bitrate == 500_000
    print(
        f"8 MHz clock, 500 kbit/s, 80 % asked: BRP {timing.brp}, TSEG1 {timing.tseg1}, "
        f"TSEG2 {timing.tseg2}, sample point {timing.sample_point:.2f} %"
    )
    frame = can.Message(is_error_frame=True, arbitration_id=0x4, data=bytes(8))
    assert frame.is_error_frame
    print("error frames are Message objects with is_error_frame=True; nothing here makes one")


if __name__ == "__main__":
    main()
