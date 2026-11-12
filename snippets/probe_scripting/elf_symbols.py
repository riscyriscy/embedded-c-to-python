"""Read a firmware global by name: ELF symbol table, DWARF size, a Probe, struct.

Run: sh fw_build.sh && python3 elf_symbols.py
"""

import logging
import struct
import sys
from dataclasses import dataclass
from typing import Any, Protocol

from elftools.dwarf.die import DIE
from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection

log = logging.getLogger("probe")


class ProbeError(Exception):
    """The probe could not read the target (bus fault, no probe, link down)."""


class Probe(Protocol):
    def read_memory(self, address: int, length: int) -> bytes: ...


class FakeProbe:
    """A target whose memory is the loadable segments of an ELF file.

    RAM holds what the C start-up code would have copied there: .data at its
    run-time address, .bss as zeros (segment memory size larger than file size).
    """

    def __init__(self, elf: ELFFile) -> None:
        self._ranges: list[tuple[int, bytes]] = []
        for seg in elf.iter_segments():
            if seg["p_type"] == "PT_LOAD":
                image = seg.data().ljust(seg["p_memsz"], b"\0")
                self._ranges.append((seg["p_vaddr"], image))

    def read_memory(self, address: int, length: int) -> bytes:
        for base, image in self._ranges:
            if base <= address and address + length <= base + len(image):
                return image[address - base : address - base + length]
        raise ProbeError(f"bus fault: no memory at {address:#010x}, {length} bytes")


@dataclass(frozen=True)
class Symbol:
    name: str
    address: int
    size: int


def find_symbol(elf: ELFFile, name: str) -> Symbol:
    table = elf.get_section_by_name(".symtab")
    if not isinstance(table, SymbolTableSection):
        raise ProbeError("no symbol table: was the ELF stripped?")
    for sym in table.get_symbol_by_name(name) or []:
        if sym["st_info"]["type"] == "STT_OBJECT":
            return Symbol(name, sym["st_value"], sym["st_size"])
    raise KeyError(f"no data symbol named {name}")


def dwarf_size(elf: ELFFile, name: str) -> int:
    """Size of the variable's type according to the DWARF debug information."""
    for cu in elf.get_dwarf_info().iter_CUs():
        for die in cu.iter_DIEs():
            if die.tag == "DW_TAG_variable" and die.attributes["DW_AT_name"].value == (
                name.encode()
            ):
                return _type_size(die)
    raise KeyError(f"no DWARF variable named {name}")


def _type_size(die: DIE) -> int:
    t = die.get_DIE_from_attribute("DW_AT_type")
    while t.tag in ("DW_TAG_typedef", "DW_TAG_volatile_type", "DW_TAG_const_type"):
        t = t.get_DIE_from_attribute("DW_AT_type")
    if t.tag == "DW_TAG_array_type":  # element size times the product of the bounds
        count = 1
        for sub in t.iter_children():
            if sub.tag == "DW_TAG_subrange_type":
                count *= sub.attributes["DW_AT_upper_bound"].value + 1
        return count * _type_size(t)
    return int(t.attributes["DW_AT_byte_size"].value)


def read_symbol(probe: Probe, elf: ELFFile, name: str, fmt: str) -> tuple[Any, ...]:
    """Read global `name` from the target and decode it with struct format `fmt`."""
    sym = find_symbol(elf, name)
    if struct.calcsize(fmt) != sym.size:
        raise ValueError(
            f"{name} is {sym.size} bytes, {fmt!r} is {struct.calcsize(fmt)}"
        )
    log.debug("read %s: %d bytes at %#x", name, sym.size, sym.address)
    return struct.unpack(fmt, probe.read_memory(sym.address, sym.size))


SYMBOLS = [
    ("g_counter", "<I"),
    ("g_config", "<BxHi"),
    ("g_samples", "<8H"),
    ("g_errors", "<I"),
]


def main(path: str) -> None:
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, format="%(message)s")
    with open(path, "rb") as f:
        elf = ELFFile(f)
        probe = FakeProbe(elf)
        for name, fmt in SYMBOLS:
            sym = find_symbol(elf, name)
            value = read_symbol(probe, elf, name, fmt)
            dwarf = dwarf_size(elf, name)
            where = f"{sym.address:#010x} {sym.size:>2} bytes"
            print(f"{name:<10} {where} (DWARF {dwarf:>2}) {value}")
        mode, rate_hz, offset_mv = read_symbol(probe, elf, "g_config", "<BxHi")
        print(f"g_config: mode {mode}, rate {rate_hz} Hz, offset {offset_mv} mV")
        for call in (
            lambda: read_symbol(probe, elf, "g_config", "<BHi"),
            lambda: probe.read_memory(0x10000000, 4),
        ):
            try:
                call()
            except (ValueError, ProbeError) as e:
                print(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "fw_probe.elf")
