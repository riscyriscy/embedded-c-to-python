"""Testing log output with pytest's caplog fixture: no handlers to configure, no files to read."""

import logging
import queue
import sys
import time

import pytest
from logging_demo import (
    BriefFormatter,
    ContextFilter,
    ContextQueueHandler,
    UtcFormatter,
    measure,
    run_context,
)


def test_measure_retries_twice_and_logs_each_retry(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.DEBUG, logger="rig"):
        assert measure() == 3.29
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert [r.attempt for r in warnings] == [0, 1]  # type: ignore[attr-defined]
    assert caplog.records[-1].getMessage() == "rail ok: 3.29 V"


def test_debug_records_are_not_captured_at_info_level(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="rig"):
        measure()
    assert all(r.levelno >= logging.INFO for r in caplog.records)


def test_context_filter_adds_run_and_dut() -> None:
    record = logging.LogRecord("rig", logging.INFO, __file__, 1, "x", None, None)
    with run_context("R-1", "SN9"):
        ContextFilter().filter(record)
    assert (record.run_id, record.dut) == ("R-1", "SN9")  # type: ignore[attr-defined]


def test_full_queue_drops_and_counts_instead_of_blocking() -> None:
    pending: queue.Queue[logging.LogRecord] = queue.Queue(maxsize=2)
    handler = ContextQueueHandler(pending)
    record = logging.LogRecord("rig", logging.INFO, __file__, 1, "x", None, None)
    for _ in range(5):
        handler.handle(record)  # returns at once, with nobody reading the queue
    assert (pending.qsize(), handler.dropped) == (2, 3)


def test_prepare_formats_arguments_before_the_caller_reuses_a_buffer() -> None:
    handler = ContextQueueHandler(queue.Queue())
    buffer = bytearray(b"\x01\x02")
    record = logging.LogRecord("rig", logging.INFO, __file__, 1, "rx %s", (buffer,), None)
    prepared = handler.prepare(record)
    buffer[:] = b"\xff\xff"  # the next receive overwrites the same buffer
    assert prepared.getMessage() == "rx bytearray(b'\\x01\\x02')"


def test_brief_formatter_hides_the_traceback_whatever_handler_formats_first() -> None:
    try:
        int("0x1F")
    except ValueError:
        record = logging.LogRecord("rig", logging.ERROR, __file__, 1, "bad", None, sys.exc_info())
    file_line = UtcFormatter("%(message)s").format(record)  # fills record.exc_text
    assert "Traceback" in file_line
    console_line = BriefFormatter("%(message)s").format(record)
    assert console_line == "bad"


@pytest.mark.skipif(not hasattr(time, "tzset"), reason="time.tzset is POSIX only")
def test_utc_formatter_ignores_the_local_time_zone(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TZ", "America/Toronto")
    time.tzset()
    try:
        record = logging.LogRecord("rig", logging.INFO, __file__, 1, "x", None, None)
        record.created = 0.0
        fmt = "%Y-%m-%d %H:%M:%S"
        assert (
            time.strftime(fmt, time.localtime(0)) == "1969-12-31 19:00:00"
        )  # the zone took effect
        assert UtcFormatter().formatTime(record, fmt) == "1970-01-01 00:00:00"
    finally:
        monkeypatch.undo()
        time.tzset()
