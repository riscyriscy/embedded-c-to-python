"""A Probe on top of pyOCD, run here against a stand-in session.

Run: sh fw_build.sh && python3 pyocd_adapter.py
"""

import inspect
import io
import re
import sys
from collections.abc import Iterator, Sequence
from contextlib import contextmanager, redirect_stdout
from importlib.metadata import version
from typing import Protocol

from elftools.elf.elffile import ELFFile
from pyocd.core.exceptions import TransferError  # type: ignore[import-untyped]
from pyocd.core.helpers import ConnectHelper  # type: ignore[import-untyped]
from pyocd.core.target import Target  # type: ignore[import-untyped]

from elf_symbols import FakeProbe, Probe, ProbeError, read_symbol


class _Target(Protocol):
    def read_memory_block8(self, addr: int, size: int) -> Sequence[int]: ...


class _Session(Protocol):
    @property
    def target(self) -> _Target: ...


class PyOcdProbe:
    """Satisfies Probe. Wraps an open pyOCD session (a context manager)."""

    def __init__(self, session: _Session) -> None:
        self._target = session.target

    def read_memory(self, address: int, length: int) -> bytes:
        try:
            return bytes(self._target.read_memory_block8(address, length))
        except TransferError as e:
            raise ProbeError(f"transfer error at {address:#010x}: {e}") from e


@contextmanager
def pyocd_probe(target: str | None = None) -> Iterator[PyOcdProbe]:
    """Open the first probe pyOCD finds, for example target='stm32f407vg'."""
    options = {"target_override": target} if target else {}
    session = ConnectHelper.session_with_chosen_probe(
        blocking=False, return_first=True, options=options
    )
    if session is None:
        raise ProbeError("no debug probe found")
    with session:  # opens the probe and the target, closes them on exit
        yield PyOcdProbe(session)


class StandInTarget:
    """Same method as pyOCD's Target, but reads from another Probe."""

    def __init__(self, probe: Probe) -> None:
        self._probe = probe
        self.calls: list[tuple[int, int]] = []

    def read_memory_block8(self, addr: int, size: int) -> list[int]:
        self.calls.append((addr, size))
        try:
            return list(self._probe.read_memory(addr, size))
        except ProbeError as e:
            raise TransferError(str(e)) from e


class StandInSession:
    def __init__(self, target: StandInTarget) -> None:
        self.target = target


def main(path: str) -> None:
    real = inspect.signature(Target.read_memory_block8)
    print(f"pyocd {version('pyocd')}: Target.read_memory_block8{real}")
    mine = inspect.signature(StandInTarget.read_memory_block8)
    print(
        "stand-in parameter names match:",
        list(mine.parameters) == list(real.parameters),
    )
    with open(path, "rb") as f:
        elf = ELFFile(f)
        target = StandInTarget(FakeProbe(elf))
        probe = PyOcdProbe(StandInSession(target))
        print("g_counter:", read_symbol(probe, elf, "g_counter", "<I"))
        print("g_samples:", read_symbol(probe, elf, "g_samples", "<8H"))
        print("calls made:", [(f"{a:#x}", n) for a, n in target.calls])
        try:
            probe.read_memory(0x10000000, 4)
        except ProbeError as e:
            print(f"ProbeError: {e}")
    says = io.StringIO()
    try:
        with redirect_stdout(says), pyocd_probe():  # this helper prints, not logs
            pass
    except ProbeError as e:
        print(f"ProbeError: {e}")
    print("pyOCD printed:", re.sub(r"\x1b\[\d+m", "", says.getvalue()).strip())


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "fw_probe.elf")
