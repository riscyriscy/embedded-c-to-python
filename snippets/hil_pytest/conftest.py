"""pytest wiring for hardware tests: --dut option, hardware marker, dut fixture.

Run: pytest -q --dut fake
"""

from collections.abc import Iterator

import pytest

from tlm100 import FakeDevice, SerialTransport, Transport, query


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--dut", help="'fake', or a serial port such as /dev/ttyUSB0")


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "hardware: needs a device, see --dut")


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if config.getoption("--dut"):
        return
    skip = pytest.mark.skip(reason="no device: pass --dut fake or --dut <port>")
    for item in items:
        if "hardware" in item.keywords:
            item.add_marker(skip)


@pytest.fixture
def dut(request: pytest.FixtureRequest) -> Iterator[Transport]:
    name: str = request.config.getoption("--dut")
    link: Transport = FakeDevice() if name == "fake" else SerialTransport(name)
    yield link  # the test body runs here, and may fail
    try:
        query(link, "RESET")  # runs after a failure or a timeout as well
    finally:
        link.close()
