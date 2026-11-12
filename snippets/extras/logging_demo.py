"""Logging for a test rig: console and file handlers, run context, JSON lines, threads, tests.

A library logs through its own named logger and never configures handlers. The application
(here main) configures handlers once. Every record carries the test run id and the DUT serial
number, set once per test with a context variable. Output is written to ./out.
Run: python3 logging_demo.py
"""

import contextvars
import copy
import json
import logging
import logging.config
import logging.handlers
import queue
import re
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

QUEUE_LIMIT = 10_000  # records waiting for the listener; more than this are dropped, not buffered

run_id = contextvars.ContextVar("run_id", default="-")
dut = contextvars.ContextVar("dut", default="-")


class ContextFilter(logging.Filter):
    """Copy the context variables onto every record, so that formatters can use them."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.run_id = run_id.get()
        record.dut = dut.get()
        return True


class UtcFormatter(logging.Formatter):
    """Time stamps in UTC, so logs from several machines line up with the instrument logs."""

    converter = staticmethod(time.gmtime)


class BriefFormatter(logging.Formatter):
    """Console format: one line per record, without the traceback (the file has it).

    Formatter.format() stores the formatted traceback in record.exc_text, and all handlers share
    one record. A handler that formats first would put its traceback into this line. So the
    traceback fields are removed from a copy before formatting.
    """

    def format(self, record: logging.LogRecord) -> str:
        brief = copy.copy(record)
        brief.exc_info = brief.exc_text = brief.stack_info = None
        return super().format(brief)


class ContextQueueHandler(logging.handlers.QueueHandler):
    """Runs in the calling thread, so it is the right place for the context filter.

    The default prepare() formats the traceback into the message text. Keeping the exception
    on the record lets each real handler decide how to show the traceback. The message is
    formatted here, in the calling thread, because the listener runs later and a caller may
    have reused a buffer that was passed as an argument.
    """

    dropped = 0  # records lost because the queue was full

    def prepare(self, record: logging.LogRecord) -> logging.LogRecord:
        record = copy.copy(record)
        record.msg = record.getMessage()
        record.args = None
        return record

    def enqueue(self, record: logging.LogRecord) -> None:
        """Never block the measurement loop: a full queue loses the record and counts it."""
        try:
            self.queue.put_nowait(record)
        except queue.Full:
            self.dropped += 1


class JsonFormatter(UtcFormatter):
    """One JSON object per line: easy to load into pandas or to grep with jq."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "logger": record.name,
            "run": getattr(record, "run_id", "-"),
            "dut": getattr(record, "dut", "-"),
            "msg": record.getMessage(),
        }
        for key in ("voltage_v", "attempt"):  # structured fields passed with extra={...}
            if hasattr(record, key):
                entry[key] = getattr(record, key)
        if record.exc_info:  # only the last line, for example "ValueError: invalid literal ..."
            entry["exc"] = self.formatException(record.exc_info).splitlines()[-1]
        return json.dumps(entry)


def configure(out_dir: Path) -> logging.handlers.QueueListener:
    out_dir.mkdir(exist_ok=True)
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "console": {
                    "()": BriefFormatter,
                    "format": "%(levelname)-7s %(name)s [%(dut)s] %(message)s",
                },
                "file": {
                    "()": UtcFormatter,
                    "format": "%(asctime)s %(levelname)s %(name)s run=%(run_id)s %(message)s",
                },
                "json": {"()": JsonFormatter},
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "console",
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "file",
                    "filename": str(out_dir / "rig.log"),
                    "maxBytes": 1_000_000,  # rotate at 1 MB, keep 3 old files
                    "backupCount": 3,
                    "encoding": "utf-8",
                },
                "json": {
                    "class": "logging.FileHandler",
                    "level": "INFO",
                    "formatter": "json",
                    "filename": str(out_dir / "rig.jsonl"),
                    "mode": "w",
                    "encoding": "utf-8",
                },
            },
            "root": {"level": "DEBUG", "handlers": ["console", "file", "json"]},
            "loggers": {"rig.noisy": {"level": "WARNING"}},  # one chatty module turned down
        }
    )
    logging.captureWarnings(True)  # warnings.warn() goes to the log too
    # Worker threads log through a queue, so a slow disk never blocks a measurement loop.
    # The listener thread owns the real handlers.
    root = logging.getLogger()
    handlers = list(root.handlers)
    q: queue.Queue[logging.LogRecord] = queue.Queue(maxsize=QUEUE_LIMIT)
    listener = logging.handlers.QueueListener(q, *handlers, respect_handler_level=True)
    queue_handler = ContextQueueHandler(q)
    queue_handler.addFilter(ContextFilter())  # runs here, in the thread that logged
    root.handlers[:] = [queue_handler]
    listener.start()
    return listener


@contextmanager
def run_context(run: str, serial: str) -> Iterator[None]:
    tokens = (run_id.set(run), dut.set(serial))
    try:
        yield
    finally:
        run_id.reset(tokens[0])
        dut.reset(tokens[1])


# --- library code: a logger per module, no configuration, lazy formatting ---
supply_log = logging.getLogger("rig.supply")
noisy_log = logging.getLogger("rig.noisy")


def read_rail(attempt: int) -> float:
    supply_log.debug("reading 3V3 rail, attempt %d", attempt)  # not formatted unless emitted
    if attempt < 2:
        raise TimeoutError("no reply from DMM")
    return 3.29


def measure() -> float:
    for attempt in range(3):
        try:
            v = read_rail(attempt)
        except TimeoutError:
            supply_log.warning("retrying after timeout", extra={"attempt": attempt})
            continue
        supply_log.info("rail ok: %.2f V", v, extra={"voltage_v": v})
        return v
    raise RuntimeError("DMM never answered")


def main() -> None:
    out = Path("out")
    out.mkdir(exist_ok=True)
    for old in out.glob("rig.log*"):  # start each demo run with a fresh log
        old.unlink()
    listener = configure(out)
    try:
        with run_context("R-0042", "SN0007"):
            measure()
            noisy_log.info("this INFO line is filtered out")
            noisy_log.warning("noisy module warning")
            # A new thread starts with an empty context (on the default builds), so the
            # record has no run id. Context.run() gives the thread a copy of this one.
            plain = threading.Thread(target=lambda: supply_log.info("thread without context"))
            plain.start()
            plain.join()
            ctx = contextvars.copy_context()
            copied = threading.Thread(
                target=ctx.run, args=(supply_log.info, "thread with copied context")
            )
            copied.start()
            copied.join()
            try:
                int("0x1F")
            except ValueError:
                supply_log.exception("cannot parse register value")  # includes the traceback
        with run_context("R-0043", "SN0008"):
            supply_log.error("rail out of range: %.2f V", 2.91)
    finally:
        listener.stop()  # flushes the queue
        logging.shutdown()

    print("--- rig.log (time removed)")
    for line in (out / "rig.log").read_text(encoding="utf-8").splitlines():
        if re.match(r"\d{4}-", line):
            print(re.sub(r"^\S+ \S+ ", "", line))
        elif line.startswith(("Traceback", "ValueError")):
            print(line)
    print("--- rig.jsonl (time removed)")
    for line in (out / "rig.jsonl").read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        record.pop("time")
        print(json.dumps(record))


if __name__ == "__main__":
    main()
