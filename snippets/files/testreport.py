"""Production-test report: limits from TOML, results from CSV, reports out.

Run: python3 testreport.py
"""

from __future__ import annotations

import csv
import json
import statistics
import tomllib
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

DATA, OUT = Path("data"), Path("out")


@dataclass
class Unit:
    serial: str
    station: str
    tested: datetime
    v3v3: float | None
    v1v8: float | None
    temp_c: float | None
    failures: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.failures


def json_default(obj: object) -> str:
    if isinstance(obj, datetime):
        return obj.isoformat()  # same "T" form as failures.csv
    raise TypeError(f"{type(obj).__name__} is not JSON serializable")


def opt_float(text: str) -> float | None:
    return float(text) if text.strip() else None  # empty CSV cell -> missing measurement


def load_units(path: Path) -> list[Unit]:
    # newline="": let csv handle line ends; utf-8-sig drops the BOM that Excel writes
    with path.open(newline="", encoding="utf-8-sig") as f:
        return [
            Unit(
                row["serial"],
                row["station"],
                datetime.fromisoformat(row["timestamp"]),
                opt_float(row["v3v3"]),
                opt_float(row["v1v8"]),
                opt_float(row["temp_c"]),
            )
            for row in csv.DictReader(f)  # each row is a dict keyed by the header line
        ]


def check(unit: Unit, limits: dict[str, Any]) -> None:
    for rail, lim in limits["rails"].items():
        value = getattr(unit, rail)  # look up the attribute named in the TOML file
        if value is None:
            unit.failures.append(f"{rail} not measured")
        elif not lim["min"] <= value <= lim["max"]:
            unit.failures.append(f"{rail} {value:.2f} V outside {lim['min']:.2f}-{lim['max']:.2f}")
    if unit.temp_c is None:
        unit.failures.append("temp not measured")
    else:
        lo, hi = limits["temperature"]["min_c"], limits["temperature"]["max_c"]
        if not lo <= unit.temp_c <= hi:  # written this way so that NaN fails too
            unit.failures.append(f"temp {unit.temp_c:.1f} C outside {lo:.1f}-{hi:.1f}")


def main() -> None:
    with (DATA / "limits.toml").open("rb") as toml_file:  # tomllib (stdlib, read-only): binary
        limits = tomllib.load(toml_file)
    units = load_units(DATA / "results.csv")
    for u in units:
        check(u, limits)

    by_station: defaultdict[str, list[Unit]] = defaultdict(list)
    for u in units:
        by_station[u.station].append(u)

    # ---- Console report: aligned columns with f-string format specs ----
    first, last = min(u.tested for u in units), max(u.tested for u in units)
    print(f"{limits['product']} production test, {first:%Y-%m-%d %H:%M} to {last:%H:%M}\n")
    header = f"{'station':<8}{'units':>6}{'pass':>6}{'yield':>8}{'3V3 mean':>10}{'3V3 sd':>9}"
    print(header + "\n" + "=" * len(header))
    summary = {}
    for station, group in sorted(by_station.items()):
        v = [u.v3v3 for u in group if u.v3v3 is not None]
        passed = sum(u.passed for u in group)  # True counts as 1
        summary[station] = {
            "units": len(group),
            "passed": passed,
            "yield": passed / len(group),
            "v3v3_mean": statistics.mean(v),
            "v3v3_stdev": statistics.stdev(v),
        }
        s = summary[station]
        print(
            f"{station:<8}{s['units']:>6}{s['passed']:>6}{s['yield']:>8.0%}"
            f"{s['v3v3_mean']:>10.3f}{s['v3v3_stdev']:>9.3f}"
        )

    failed = [u for u in units if not u.passed]
    print(f"\n{len(failed)} of {len(units)} units failed:")
    for u in sorted(failed, key=lambda u: u.serial):
        print(f"  {u.serial}  {u.station}  {'; '.join(u.failures)}")

    # ---- Output files: CSV for the MES, JSON for dashboards, Markdown for the wiki ----
    OUT.mkdir(exist_ok=True)
    with (OUT / "failures.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["serial", "station", "tested", "failures"])
        w.writeheader()
        for u in failed:
            w.writerow(
                {
                    "serial": u.serial,
                    "station": u.station,
                    "tested": u.tested.isoformat(),
                    "failures": "; ".join(u.failures),
                }
            )

    report = {
        "product": limits["product"],
        "stations": summary,
        "failed": [asdict(u) for u in failed],
    }
    (OUT / "summary.json").write_text(
        json.dumps(report, indent=2, default=json_default), encoding="utf-8"
    )

    lines = [
        "| Serial | Station | 3V3 (V) | 1V8 (V) | Temp (C) | Result |",
        "|---|---|---:|---:|---:|---|",
    ]

    def fmt(x: float | None, spec: str) -> str:
        return "n/a" if x is None else format(x, spec)  # format() applies a format spec

    for u in units:
        result = "PASS" if u.passed else "**FAIL**: " + "; ".join(u.failures)
        lines.append(
            f"| {u.serial} | {u.station} | {fmt(u.v3v3, '.2f')} | {fmt(u.v1v8, '.2f')} "
            f"| {fmt(u.temp_c, '.1f')} | {result} |"
        )
    (OUT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT / 'failures.csv'}, {OUT / 'summary.json'} and {OUT / 'report.md'}")


if __name__ == "__main__":
    main()
