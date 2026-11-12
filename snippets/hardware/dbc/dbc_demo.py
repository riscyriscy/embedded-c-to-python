"""cantools: one DBC file describes the frames for both ends of the bus."""
import struct

import can
import cantools

db = cantools.database.load_file("engine.dbc")
for m in db.messages:
    sigs = [f"{s.name} [{s.start}:{s.length}] x{s.scale}+{s.offset} {s.unit or '-'}" for s in m.signals]
    print(f"0x{m.frame_id:03x} {m.name:<11} {m.length} bytes  " + ", ".join(sigs))

temp = db.get_message_by_name("DeviceTemp")
raw = temp.encode({"Temperature": 28.45, "Counter": 7})
print("encode ", raw.hex(" "), "equals struct:", raw == struct.pack("<hB", 2845, 7))
print("decode ", temp.decode(bytes.fromhex("1d0b07")))
print("lookup ", db.get_message_by_frame_id(0x1A0).name)

pump = db.get_message_by_name("PumpCommand")
print("pump   ", pump.encode({"Speed": 1500.0, "Enable": 1}).hex(" "))
for bad in ({"Speed": 1800.0, "Enable": 1}, {"Speed": 100.0}):
    try:
        pump.encode(bad)
    except Exception as e:                     # cantools.database.errors.EncodeError
        print(f"error   {type(e).__name__}: {e}")
print("lenient", pump.encode({"Speed": 1800.0, "Enable": 1}, strict=False).hex(" "))
try:
    pump.encode({"Speed": 3000.0, "Enable": 1}, strict=False)
except Exception as e:                         # the 12-bit field cannot hold 6000
    print(f"overflow {type(e).__name__}: {e}")
try:
    temp.decode(b"\x1d\x0b")                   # frame shorter than the DBC length
except Exception as e:
    print(f"short   {type(e).__name__}: {e}")

# With python-can: the database decodes whatever the bus delivers.
with can.Bus(interface="virtual", channel="dbc", receive_own_messages=True) as bus:
    frame = bytes.fromhex("1d0b07")
    bus.send(can.Message(arbitration_id=0x1A0, is_extended_id=False, data=frame))
    msg = bus.recv(timeout=0.1)
    print("on bus ", db.decode_message(msg.arbitration_id, msg.data))
    try:
        db.decode_message(0x333, b"\x00")
    except KeyError as e:
        print(f"unknown KeyError: {e}")
