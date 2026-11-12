"""A resilient request/reply link: timeouts, retries with backoff, reconnection, deadline.

Wraps any transport that has query() and close(), such as SerialTransport from
serial_demo.py. It tells three failures apart, checks that the same device answers
after a reconnect, and gives up at a deadline. No hardware is needed: main() runs it
against a scripted fake instrument and a fake clock, so nothing really sleeps.
Run: python3 resilient_link.py
"""

import random
import time
from collections import deque
from collections.abc import Callable
from typing import Protocol


class Transport(Protocol):
    def query(self, command: str) -> str: ...
    def close(self) -> None: ...


class LinkError(Exception):
    """The command did not complete within the allowed attempts and time."""


class DeviceChanged(LinkError):
    """After a reconnect, a different device answered the identity query."""


class ResilientLink:
    """query() with retries. A timeout means the device is there but silent: ask again on
    the same link. An OSError (pyserial's SerialException is one) means the link is gone:
    close it, wait, reconnect, check the identity, ask again. The transport must raise OSError
    for every lost-link case: SerialTransport converts termios.error, which is not an OSError."""

    def __init__(
        self,
        connect: Callable[[], Transport],
        *,
        attempts: int = 4,
        base_delay_s: float = 0.1,
        max_delay_s: float = 2.0,
        deadline_s: float = 10.0,
        identity_command: str = "*IDN?",
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
        rng: random.Random | None = None,
    ) -> None:
        self._connect = connect
        self.attempts = attempts
        self.base_delay_s = base_delay_s
        self.max_delay_s = max_delay_s
        self.deadline_s = deadline_s
        self._identity_command = identity_command
        self._sleep = sleep
        self._clock = clock
        self._rng = rng or random.Random()
        self._link: Transport | None = None
        self.identity: str | None = None  # what the first connection reported
        self.reconnects = 0

    def _ensure_link(self) -> Transport:
        if self._link is not None:
            return self._link
        link = self._connect()
        try:
            reply = link.query(self._identity_command)
        except BaseException:
            link.close()
            raise
        if self.identity is None:
            self.identity = reply
        elif reply != self.identity:
            link.close()
            raise DeviceChanged(f"expected {self.identity!r}, got {reply!r}")
        else:
            self.reconnects += 1
        self._link = link
        return link

    def _drop(self) -> None:
        if self._link is not None:
            try:
                self._link.close()
            except OSError:
                pass  # closing a link that is already gone is not an error
            self._link = None

    def query(self, command: str, *, idempotent: bool = True) -> str:
        """Send one command. Repeat it only if it is safe to: a command that changes the
        device (idempotent=False) is sent once, because a timeout does not tell you whether
        the device acted on it."""
        start = self._clock()
        last: Exception | None = None
        for attempt in range(1, self.attempts + 1):
            try:
                link = self._ensure_link()
            except DeviceChanged:
                raise
            except OSError as exc:  # includes TimeoutError: connecting or the identity failed
                last = exc
                self._drop()
            else:
                try:
                    return link.query(command)
                except OSError as exc:  # TimeoutError is an OSError too
                    last = exc
                    if not isinstance(exc, TimeoutError):
                        self._drop()  # unplugged or closed: reconnect on the next attempt
                    # A timeout keeps the link, because the device is there but silent.
                    if not idempotent:
                        raise LinkError(f"{command!r} failed and is not safe to repeat") from exc
            if attempt == self.attempts:
                break
            delay = min(self.max_delay_s, self.base_delay_s * 2 ** (attempt - 1))
            delay *= self._rng.uniform(0.5, 1.0)  # jitter, so several rigs do not retry in step
            if self._clock() - start + delay > self.deadline_s:
                raise LinkError(f"{command!r}: deadline of {self.deadline_s} s reached") from last
            self._sleep(delay)
        raise LinkError(f"{command!r} failed after {attempt} attempts") from last

    def close(self) -> None:
        self._drop()


# ---- a scripted fake, for the demo and for the tests ---------------------------------------
class FakeTransport:
    def __init__(self, bench: "FakeBench") -> None:
        self.bench = bench
        self.dead = False

    def query(self, command: str) -> str:
        if self.dead:
            raise OSError("port is gone")
        if command == "*IDN?":
            return self.bench.identity
        self.bench.queries += 1
        action = self.bench.plan.popleft() if self.bench.plan else "ok"
        if action == "timeout":
            raise TimeoutError(f"no reply to {command!r}")
        if action == "unplug":
            self.dead = True
            raise OSError("device unplugged")
        return "ERR 1" if action == "err" else "28.4"

    def close(self) -> None:
        self.dead = True


class FakeBench:
    """Scripts what the instrument does to each query: 'ok', 'err', 'timeout' or 'unplug'."""

    def __init__(self, *plan: str, identity: str = "TLM-100,SN0007") -> None:
        self.plan = deque(plan)
        self.identity = identity
        self.queries = 0
        self.connects = 0

    def connect(self) -> FakeTransport:
        self.connects += 1
        return FakeTransport(self)


class FakeTime:
    """A clock that only moves when the link sleeps."""

    def __init__(self) -> None:
        self.now = 0.0
        self.delays: list[float] = []

    def sleep(self, seconds: float) -> None:
        self.delays.append(round(seconds, 3))
        self.now += seconds

    def clock(self) -> float:
        return self.now


def make_link(
    bench: FakeBench,
    *,
    attempts: int = 4,
    base_delay_s: float = 0.1,
    deadline_s: float = 10.0,
) -> tuple[ResilientLink, FakeTime]:
    fake = FakeTime()
    link = ResilientLink(
        bench.connect,
        attempts=attempts,
        base_delay_s=base_delay_s,
        deadline_s=deadline_s,
        sleep=fake.sleep,
        clock=fake.clock,
        rng=random.Random(7),
    )
    return link, fake


def main() -> None:
    bench = FakeBench("timeout", "timeout", "ok")
    link, fake = make_link(bench)
    print(
        "1. two timeouts:", link.query("TEMP?"), "delays", fake.delays, "connects", bench.connects
    )

    bench = FakeBench("unplug", "ok")
    link, fake = make_link(bench)
    print("2. unplugged:", link.query("TEMP?"), "delays", fake.delays, "connects", bench.connects)

    bench = FakeBench("ok", "unplug")
    link, fake = make_link(bench)
    link.query("TEMP?")
    bench.identity = "TLM-100,SN0099"  # another unit is plugged in while the link is down
    try:
        link.query("TEMP?")
    except DeviceChanged as exc:
        print("3. swapped unit:", exc)

    bench = FakeBench(*["timeout"] * 10)
    link, fake = make_link(bench)
    try:
        link.query("TEMP?")
    except LinkError as exc:
        print("4. silent device:", exc, "| delays", fake.delays, "| sent", bench.queries)

    bench = FakeBench("timeout", "ok")
    link, fake = make_link(bench)
    try:
        link.query("RATE 250", idempotent=False)
    except LinkError as exc:
        print("5. not repeated:", exc, "| sent", bench.queries)

    bench = FakeBench(*["timeout"] * 10)
    link, fake = make_link(bench, attempts=10, base_delay_s=1.0, deadline_s=3.0)
    try:
        link.query("TEMP?")
    except LinkError as exc:
        print("6. deadline:", exc, "| delays", fake.delays, "| sent", bench.queries)


if __name__ == "__main__":
    main()
