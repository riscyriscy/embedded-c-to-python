from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Telemetry(_message.Message):
    __slots__ = ("timestamp_ms", "temperature_cdeg", "supply_mv", "status")
    TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
    TEMPERATURE_CDEG_FIELD_NUMBER: _ClassVar[int]
    SUPPLY_MV_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    timestamp_ms: int
    temperature_cdeg: int
    supply_mv: int
    status: int
    def __init__(self, timestamp_ms: _Optional[int] = ..., temperature_cdeg: _Optional[int] = ..., supply_mv: _Optional[int] = ..., status: _Optional[int] = ...) -> None: ...

class TelemetryV2(_message.Message):
    __slots__ = ("timestamp_ms", "temperature_cdeg", "supply_mv", "status", "uptime_s")
    TIMESTAMP_MS_FIELD_NUMBER: _ClassVar[int]
    TEMPERATURE_CDEG_FIELD_NUMBER: _ClassVar[int]
    SUPPLY_MV_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    UPTIME_S_FIELD_NUMBER: _ClassVar[int]
    timestamp_ms: int
    temperature_cdeg: int
    supply_mv: int
    status: int
    uptime_s: int
    def __init__(self, timestamp_ms: _Optional[int] = ..., temperature_cdeg: _Optional[int] = ..., supply_mv: _Optional[int] = ..., status: _Optional[int] = ..., uptime_s: _Optional[int] = ...) -> None: ...
