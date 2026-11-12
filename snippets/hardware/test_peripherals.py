import inspect

import pytest

from peripherals import (
    FakeEdge,
    FakeI2c,
    FakeSpiFlash,
    I2cBus,
    jedec_id,
    read_temperature,
)


def test_temperature_is_signed() -> None:
    assert read_temperature(FakeI2c({0x00: 0xFF00})) == -2.0


def test_missing_device_is_oserror() -> None:
    with pytest.raises(OSError, match="Remote I/O"):
        read_temperature(FakeI2c({}), addr=0x49)


def test_jedec_id() -> None:
    assert jedec_id(FakeSpiFlash()) == "EF 40 18"


def test_edge_times_out() -> None:
    assert FakeEdge().wait_edge(0.01) is False


def test_fake_has_the_same_signature_as_smbus2() -> None:
    smbus2 = pytest.importorskip("smbus2")  # Linux only: the module imports fcntl
    real = inspect.signature(smbus2.SMBus.read_i2c_block_data)
    fake = inspect.signature(FakeI2c.read_i2c_block_data)
    assert list(real.parameters) == list(fake.parameters)


def test_protocol_accepts_smbus2_type() -> None:
    smbus2 = pytest.importorskip("smbus2")

    def takes(bus: I2cBus) -> None: ...

    takes(smbus2.SMBus.__new__(smbus2.SMBus))  # typing only: no device is opened
