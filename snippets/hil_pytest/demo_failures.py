"""Two tests that go wrong on purpose. Run: pytest -q --dut fake demo_failures.py"""

import pytest

from tlm100 import Transport, query


@pytest.mark.hardware
def test_wrong_expectation(dut: Transport) -> None:
    assert query(dut, "TEMP?") == "T=9999"


@pytest.mark.hardware
@pytest.mark.timeout(1)
def test_locked_up_firmware(dut: Transport) -> None:
    query(dut, "HANG")  # the reply never comes
