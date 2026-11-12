"""Hardware tests for the TLM-100. Run: pytest -q --dut fake"""

from pathlib import Path

import pytest

from tlm100 import Transport, parse_temp, query


def test_parse_temp() -> None:  # pure logic: runs with or without a device
    assert parse_temp("T=2534") == 25.34


@pytest.mark.hardware
def test_identity(dut: Transport) -> None:
    product, _serial, fw = query(dut, "ID?").split(",")
    assert (product, fw) == ("TLM-100", "1.10.0")


@pytest.mark.hardware
def test_temperature_is_plausible(dut: Transport) -> None:
    assert 15.0 <= parse_temp(query(dut, "TEMP?")) <= 35.0


@pytest.mark.hardware
def test_result_file(
    dut: Transport, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TLM_OPERATOR", "bench-3")  # undone when the test ends
    result = tmp_path / "result.txt"  # a fresh directory per test
    result.write_text(f"{query(dut, 'ID?')} {query(dut, 'TEMP?')}\n")
    assert result.read_text().startswith("TLM-100,TLM100-0007")
