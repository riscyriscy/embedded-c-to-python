"""construct: describe a binary format once, and get parse and build from the same description.

The description below is the frame format of the frametool package (Phase 5): type u8, seq u8,
payload length u16, payload, CRC-16 of everything before it. The script checks it against the
hand-written struct code in frametool. Run: python3 construct_demo.py   (needs: uv sync)
"""

import construct as c  # type: ignore[import-untyped]  # construct has no type stubs
from frametool.crc16 import crc16
from frametool.protocol import Frame, MessageType, Telemetry, TelemetryStatus

# Telemetry payload (9 bytes, little-endian). ExprAdapter converts between wire units and floats.
Status = c.FlagsEnum(c.Int8ul, OVER_TEMP=1, UNDER_VOLTAGE=2, SENSOR_FAULT=4)
Telemetry_ = c.Struct(
    "uptime_ms" / c.Int32ul,
    "temperature_c"
    / c.ExprAdapter(c.Int16sl, lambda raw, _: raw / 100, lambda v, _: round(v * 100)),
    "supply_v" / c.ExprAdapter(c.Int16ul, lambda raw, _: raw / 1000, lambda v, _: round(v * 1000)),
    "status" / Status,
)
SetRate = c.Struct("rate_hz" / c.Int16ul)


def exact(layout: c.Struct) -> c.Struct:
    """The same fields plus Terminated, so that bytes left over inside the payload are an error."""
    return c.Struct(*layout.subcons, c.Terminated)


Type = c.Enum(c.Int8ul, PING=0x01, PONG=0x02, TELEMETRY=0x10, SET_RATE=0x20)

# Prefixed(Int16ul, x): the length field, then x inside exactly that many bytes. RawCopy keeps
# the raw bytes of the fields so that Checksum can compute the CRC over them.
Frame_ = c.Struct(
    "fields"
    / c.RawCopy(
        c.Struct(
            "type" / Type,
            "seq" / c.Int8ul,
            "payload"
            / c.Prefixed(
                c.Int16ul,
                c.Switch(
                    c.this.type,
                    {"TELEMETRY": exact(Telemetry_), "SET_RATE": exact(SetRate)},
                    default=c.GreedyBytes,
                ),
            ),
        )
    ),
    "crc" / c.Checksum(c.Int16ul, lambda data: crc16(data), c.this.fields.data),
)

# A control register: bit fields, most significant bit first (BitStruct reads MSB to LSB)
Ctrl = c.BitStruct("reserved" / c.Padding(4), "mode" / c.BitsInteger(3), "enable" / c.Flag)


def struct_telemetry(raw: bytes) -> Telemetry:
    return Telemetry.from_bytes(Frame.from_bytes(raw).payload)


def main() -> None:
    telemetry = Telemetry(
        123456, 28.45, 3.3, TelemetryStatus.OVER_TEMP | TelemetryStatus.SENSOR_FAULT
    )
    wire = Frame(MessageType.TELEMETRY, 7, telemetry.to_bytes()).to_bytes()  # made by struct code

    # 1. Parse the bytes that the hand-written code made
    f = Frame_.parse(wire)
    p = f.fields.value.payload
    flags = sorted(name for name, on in p.status.items() if on and not name.startswith("_"))
    print(f.fields.value.type, f.fields.value.seq, p.uptime_ms, p.temperature_c, p.supply_v, flags)
    print("crc ok:", f.crc == crc16(f.fields.data), "| sizeof telemetry:", Telemetry_.sizeof())

    # 2. Build from a dict: length and CRC are computed, and the bytes match the struct version
    built = Frame_.build(
        {
            "fields": {
                "value": {
                    "type": "TELEMETRY",
                    "seq": 7,
                    "payload": {
                        "uptime_ms": 123456,
                        "temperature_c": 28.45,
                        "supply_v": 3.3,
                        "status": {"OVER_TEMP": True, "SENSOR_FAULT": True},
                    },
                }
            }
        }
    )
    print("built equals struct version:", built == wire, "| length", len(built))

    # 3. Errors are exceptions with a field path
    bad = bytearray(wire)
    bad[5] ^= 0x40
    for label, data in (("bad crc", bytes(bad)), ("truncated", wire[:8])):
        try:
            Frame_.parse(data)
        except c.ConstructError as exc:
            print(f"{label}: {type(exc).__name__}")

    # 4. An unknown payload type is kept as raw bytes, as frametool's Frame does
    other = Frame_.build({"fields": {"value": {"type": "PING", "seq": 1, "payload": b"\xde\xad"}}})
    print(other.hex(" "), "->", Frame_.parse(other).fields.value.payload)

    # 5. A payload longer than its layout: struct raises, and so does construct because of exact()
    body = bytes([0x10, 7]) + (12).to_bytes(2, "little") + telemetry.to_bytes() + b"\0\0\0"
    long_frame = body + crc16(body).to_bytes(2, "little")
    for label, parse in (("struct", struct_telemetry), ("construct", Frame_.parse)):
        try:
            parse(long_frame)
            print(f"12-byte telemetry payload, {label}: accepted")
        except Exception as exc:  # the two libraries raise different classes
            print(
                f"12-byte telemetry payload, {label}: {type(exc).__module__}.{type(exc).__name__}"
            )

    # 6. Bit fields
    reg = Ctrl.parse(b"\x0b")  # 0000 101 1
    print(reg.mode, reg.enable, Ctrl.build({"mode": 5, "enable": True}).hex())


if __name__ == "__main__":
    main()
