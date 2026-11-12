"""Classify test readings against limits. Run: uv run pytest (see ci.sh)."""

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class Limit:
    """The accepted range of one channel, ends included."""

    low: float
    high: float


def classify(value: float, limit: Limit) -> str:
    """Return PASS, LOW, HIGH or NAN."""
    if math.isnan(value):
        return "NAN"
    if value < limit.low:
        return "LOW"
    if value > limit.high:
        return "HIGH"
    return "PASS"


def parse_reading(line: str) -> tuple[str, float]:
    """Split 'VBAT=3.71' into ('VBAT', 3.71)."""
    name, sep, text = line.strip().partition("=")
    if not sep:
        raise ValueError(f"no '=' in {line!r}")
    return name, float(text)


def verdict(lines: Iterable[str], limits: Mapping[str, Limit]) -> bool:
    """True when every reading of a known channel passes; unknown ones are skipped."""
    ok = True
    for line in lines:
        name, value = parse_reading(line)
        if name in limits:
            ok = ok and classify(value, limits[name]) == "PASS"
    return ok
