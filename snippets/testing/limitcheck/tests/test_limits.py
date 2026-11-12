"""Tests for limitcheck. Run: uv run pytest -q"""

import pytest

from limitcheck.limits import Limit, classify, parse_reading, verdict

VBAT = Limit(3.0, 4.2)


@pytest.mark.parametrize(
    ("value", "expected"),
    [(3.0, "PASS"), (4.2, "PASS"), (2.99, "LOW"), (4.21, "HIGH")],
)
def test_classify_edges(value: float, expected: str) -> None:
    assert classify(value, VBAT) == expected


def test_parse_reading() -> None:
    assert parse_reading(" VBAT=3.71\n") == ("VBAT", 3.71)


def test_parse_reading_without_equals_sign() -> None:
    with pytest.raises(ValueError, match="no '='"):
        parse_reading("VBAT 3.71")


def test_verdict_fails_when_one_channel_fails() -> None:
    limits = {"VBAT": VBAT, "TEMP": Limit(-10.0, 60.0)}
    assert verdict(["VBAT=3.71", "TEMP=24.5"], limits)
    assert not verdict(["VBAT=3.71", "TEMP=75"], limits)
