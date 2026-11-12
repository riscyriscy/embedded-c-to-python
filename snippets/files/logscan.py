"""Scan a UART log: parse, filter, summarise, write results.

Run: python3 logscan.py data/uart.log
"""

from __future__ import annotations

import argparse
import csv
import enum
import re
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

LINE = re.compile(
    r"^\[(?P<h>\d\d):(?P<m>\d\d):(?P<s>\d\d\.\d{3})\] "
    r"(?P<level>DBG|INF|WRN|ERR) (?P<module>\w+): (?P<msg>.*)$"
)
VOLTS = re.compile(r"(\d+\.\d+) V\b")  # a number followed by " V"


class Level(enum.IntEnum):  # IntEnum: levels compare numerically, so >= WRN works
    DBG = 0
    INF = 1
    WRN = 2
    ERR = 3


@dataclass(frozen=True, slots=True)
class Entry:
    t: float  # seconds since boot
    level: Level
    module: str
    msg: str

    def __str__(self) -> str:
        return f"{self.t:9.3f}s  {self.level.name}  {self.module:<8} {self.msg}"


def parse(path: Path, rejects: list[str]) -> Iterator[Entry]:
    # errors="replace": UART captures contain line noise that is not valid UTF-8
    with path.open(encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f, start=1):  # streams line by line: fine for GB-size logs
            m = LINE.match(line.rstrip("\n"))
            if m is None:
                rejects.append(f"line {lineno}: {line.strip()!r}")
                continue
            t = int(m["h"]) * 3600 + int(m["m"]) * 60 + float(m["s"])
            yield Entry(t, Level[m["level"]], m["module"], m["msg"])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("log", type=Path)
    ap.add_argument("--min-level", choices=[lv.name for lv in Level], default="WRN")
    ap.add_argument("--out", type=Path, default=Path("out"))
    args = ap.parse_args()

    rejects: list[str] = []
    entries = list(parse(args.log, rejects))
    threshold = Level[args.min_level]
    flagged = [e for e in entries if e.level >= threshold]

    # ---- Formatted console report ----
    print(
        f"{args.log.name}: {len(entries)} entries, {len(rejects)} unparsed, "
        f"span {entries[-1].t - entries[0].t:.3f} s"
    )
    for r in rejects:
        print(f"  skipped {r}")

    counts = Counter((e.module, e.level) for e in entries)
    modules = sorted({e.module for e in entries})
    print(f"\n{'module':<8}" + "".join(f"{lv.name:>5}" for lv in Level) + f"{'total':>7}")
    print("-" * (8 + 5 * len(Level) + 7))
    for mod in modules:
        row = [counts[mod, lv] for lv in Level]
        print(f"{mod:<8}" + "".join(f"{n or '.':>5}" for n in row) + f"{sum(row):>7}")

    print(f"\n{threshold.name} and above:")
    for e in flagged:
        print(f"  {e}")

    volts = [float(v) for e in entries if e.module == "pm" for v in VOLTS.findall(e.msg)]
    print(f"\nsupply readings: {volts}  min {min(volts):.2f} V  max {max(volts):.2f} V")
    resets = [e.msg.rpartition("=")[2] for e in entries if "reset cause" in e.msg]
    print(f"boots: {len(resets)}  causes: {', '.join(resets)}")

    # ---- Files for other tools: filtered log and per-module CSV summary ----
    args.out.mkdir(exist_ok=True)
    (args.out / "flagged.log").write_text("".join(f"{e}\n" for e in flagged), encoding="utf-8")
    with (args.out / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["module", *(lv.name for lv in Level)])
        w.writerows([mod, *(counts[mod, lv] for lv in Level)] for mod in modules)
    print(f"\nwrote {args.out / 'flagged.log'} and {args.out / 'summary.csv'}")


if __name__ == "__main__":
    main()
