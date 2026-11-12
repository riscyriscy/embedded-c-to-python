"""One telemetry record as a packed struct, a construct Struct and a protobuf message.

Run: python3 protobuf_compare.py   (needs: uv sync; telemetry_pb2.py is generated from telemetry.proto)
"""

import struct
import timeit

import telemetry_pb2
from construct import (  # type: ignore[import-untyped]
    ConstructError,
    Int8ul,
    Int16sl,
    Int16ul,
    Int32ul,
    Struct,
)

RECORD = {"timestamp_ms": 123456, "temperature_cdeg": -1234, "supply_mv": 3301, "status": 2}

# 1. The same record in three encodings --------------------------------------------------------
PACKED = struct.Struct("<IhHB")  # the wire layout of telemetry_t
CONSTRUCT = Struct(
    "timestamp_ms" / Int32ul,
    "temperature_cdeg" / Int16sl,
    "supply_mv" / Int16ul,
    "status" / Int8ul,
)

raw = PACKED.pack(*RECORD.values())
built = CONSTRUCT.build(RECORD)
msg = telemetry_pb2.Telemetry(**RECORD)
encoded = msg.SerializeToString()
print(f"struct     {len(raw):2d} bytes  {raw.hex(' ')}")
print(f"construct  {len(built):2d} bytes  {built.hex(' ')}  same as struct: {built == raw}")
print(f"protobuf   {len(encoded):2d} bytes  {encoded.hex(' ')}")

# Protobuf leaves out a field that has its default value (0), so an idle record is smaller
idle = telemetry_pb2.Telemetry(timestamp_ms=1000, supply_mv=3300).SerializeToString()
print(f"protobuf, idle record (status 0, temperature not set): {len(idle)} bytes, struct always 9")

# 2. Decode back, and what a decoder does with bytes it does not expect ------------------------
back = telemetry_pb2.Telemetry.FromString(encoded)
print("protobuf decode:", back.timestamp_ms, back.temperature_cdeg, back.supply_mv, back.status)

new = telemetry_pb2.TelemetryV2(**RECORD, uptime_s=86_400).SerializeToString()
old_reader = telemetry_pb2.Telemetry.FromString(new)  # a reader built before uptime_s existed
print(
    f"protobuf: old reader on {len(new)}-byte V2 message ->", old_reader.supply_mv, "mV, no error"
)
new_struct = struct.Struct("<IhHBI").pack(*RECORD.values(), 86_400)
try:
    PACKED.unpack(new_struct)
except struct.error as exc:
    print(f"struct: old reader on {len(new_struct)}-byte V2 record ->", exc)
# construct parses the first 9 bytes of the 13-byte record and ignores the rest
parsed = CONSTRUCT.parse(new_struct)
print(
    f"construct: old reader on {len(new_struct)}-byte V2 record ->",
    parsed.supply_mv,
    "mV, no error",
)

# 2a. Zero against absent: proto3 leaves out a field that equals its default, unless it is
# declared optional. temperature_cdeg is optional, status is not.
zero = telemetry_pb2.Telemetry(timestamp_ms=1000, temperature_cdeg=0, supply_mv=3300, status=0)
zero_bytes = zero.SerializeToString()
for label, data in [("temperature 0 set", zero_bytes), ("temperature not set", idle)]:
    has = telemetry_pb2.Telemetry.FromString(data).HasField("temperature_cdeg")
    print(f"protobuf, {label}: {len(data)} bytes, HasField('temperature_cdeg') {has}")
try:
    zero.HasField("status")  # a plain proto3 field has no presence: 0 and absent look the same
except ValueError as exc:
    print("protobuf: HasField('status') ->", exc)

# 2b. A value that does not fit in 16 bits: protobuf has no 16-bit type, so uint32 takes it ------
too_big = telemetry_pb2.Telemetry(supply_mv=70_000).SerializeToString()
print("protobuf: supply_mv 70000 ->", telemetry_pb2.Telemetry.FromString(too_big).supply_mv)
try:
    struct.pack("<H", 70_000)
except struct.error as exc:
    print("struct: pack('<H', 70000) ->", exc)
try:
    Int16ul.build(70_000)
except ConstructError as exc:
    print("construct: Int16ul.build(70000) ->", type(exc).__name__)

# 3. Decode speed, best of 5 runs of 100,000 calls ----------------------------------------------
n = 100_000
for label, fn in [
    ("struct", lambda: PACKED.unpack(raw)),
    ("construct", lambda: CONSTRUCT.parse(raw)),
    ("protobuf", lambda: telemetry_pb2.Telemetry.FromString(encoded)),
]:
    best = min(timeit.repeat(fn, number=n, repeat=5)) / n * 1e6
    print(f"decode with {label:9s}{best:6.2f} us")
