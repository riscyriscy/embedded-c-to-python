"""Hardware-free tests for ResilientLink. Run: uv run pytest -q hardware/test_resilient_link.py"""

import pytest
from resilient_link import DeviceChanged, FakeBench, LinkError, make_link


def test_timeouts_are_retried_on_the_same_link() -> None:
    bench = FakeBench("timeout", "timeout", "ok")
    link, fake = make_link(bench)
    assert link.query("TEMP?") == "28.4"
    assert bench.connects == 1  # the link was kept
    assert len(fake.delays) == 2
    assert fake.delays[0] <= 0.1 and fake.delays[1] <= 0.2  # backoff doubles, jitter only shortens


def test_unplug_reconnects_and_checks_identity() -> None:
    bench = FakeBench("unplug", "ok")
    link, _ = make_link(bench)
    assert link.query("TEMP?") == "28.4"
    assert bench.connects == 2
    assert link.reconnects == 1


def test_a_different_device_is_not_accepted() -> None:
    bench = FakeBench("ok", "unplug")
    link, _ = make_link(bench)
    link.query("TEMP?")
    bench.identity = "TLM-100,SN0099"
    with pytest.raises(DeviceChanged):
        link.query("TEMP?")


def test_gives_up_after_the_attempt_limit() -> None:
    bench = FakeBench(*["timeout"] * 10)
    link, fake = make_link(bench)
    with pytest.raises(LinkError, match="after 4 attempts"):
        link.query("TEMP?")
    assert bench.queries == 4
    assert len(fake.delays) == 3  # no sleep after the last attempt


def test_a_command_that_changes_the_device_is_sent_once() -> None:
    bench = FakeBench("timeout", "ok")
    link, _ = make_link(bench)
    with pytest.raises(LinkError, match="not safe to repeat"):
        link.query("RATE 250", idempotent=False)
    assert bench.queries == 1


def test_the_deadline_wins_over_the_attempt_limit() -> None:
    bench = FakeBench(*["timeout"] * 10)
    link, fake = make_link(bench, attempts=10, base_delay_s=1.0, deadline_s=3.0)
    with pytest.raises(LinkError, match="deadline"):
        link.query("TEMP?")
    assert sum(fake.delays) <= 3.0
    assert bench.queries < 10


def test_an_error_reply_is_returned_not_retried() -> None:
    # The device answered, so the link worked. Whether "ERR 1" is acceptable is for the caller.
    bench = FakeBench("err")
    link, fake = make_link(bench)
    assert link.query("BOGUS") == "ERR 1"
    assert bench.queries == 1
    assert fake.delays == []
