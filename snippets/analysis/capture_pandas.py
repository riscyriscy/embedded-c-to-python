"""Analyse a UART log and a captured telemetry stream with pandas.

The capture comes from the simulated device of frametool: 10 Hz, every 7th frame corrupted, and a
1.2 s outage that the script cuts out of the byte stream. Run: python3 capture_pandas.py
"""

from pathlib import Path

import pandas as pd
from frametool.device import make_frame
from frametool.link import FrameSplitter
from frametool.protocol import Telemetry, TelemetryStatus

LOG = Path(__file__).parent.parent / "files" / "data" / "uart.log"
LINE = r"^\[(?P<t>[\d:.]+)\] (?P<level>[A-Z]{3}) (?P<module>\w+): (?P<text>.*)$"


def load_log(path: Path) -> pd.DataFrame:
    with path.open(encoding="utf-8", errors="replace") as f:  # the log has a line of noise
        lines = pd.Series([line.rstrip("\n") for line in f])
    table = lines.str.extract(LINE)
    print(
        f"{len(lines)} lines, {table['t'].notna().sum()} parsed, {table['t'].isna().sum()} not log lines"
    )
    table = table.dropna()
    table.index = pd.Index(pd.to_timedelta(table.pop("t")).dt.total_seconds(), name="time_s")
    return table


def load_capture() -> pd.DataFrame:
    frames = (
        make_frame(i, (i + 1) * 100, corrupt=i % 7 == 6) for i in range(600) if not 310 <= i < 322
    )
    splitter = FrameSplitter()
    rows = [Telemetry.from_bytes(f.payload) for f in splitter.feed(b"".join(frames))]
    print(f"{splitter.stats.good} frames kept, {splitter.stats.bad_crc} dropped for a bad CRC")
    uptime_ms = [t.uptime_ms for t in rows]
    table = pd.DataFrame(
        {
            "t_s": [ms / 1000 for ms in uptime_ms],
            "temperature_c": [t.temperature_c for t in rows],
            "over_temp": [bool(t.status & TelemetryStatus.OVER_TEMP) for t in rows],
        },
        index=pd.to_timedelta(uptime_ms, unit="ms"),  # a time index enables resample and rolling
    )
    return table


def main() -> None:
    log = load_log(LOG)
    print(log.groupby(["module", "level"]).size().unstack(fill_value=0), "\n")
    print(log[log["level"] == "ERR"][["module", "text"]], "\n")

    cap = load_capture()
    gap = cap["t_s"].diff()
    single = gap[(gap > 0.15) & (gap <= 0.5)]
    outage = gap[gap > 0.5]
    print(f"\n{len(single)} single-frame dropouts of {single.iloc[0]:.1f} s")
    for end, length in zip(cap["t_s"][outage.index], outage):
        print(f"outage from {end - length:.1f} s to {end:.1f} s")

    windows = cap["temperature_c"].resample("10s").agg(["mean", "min", "max", "count"])
    windows.index = pd.to_timedelta(windows.index).total_seconds().rename("window_s")
    print("\n", windows.round(2), sep="")

    smooth = cap["temperature_c"].rolling("3s").mean()
    peak = int(smooth.to_numpy().argmax())
    print(f"\nrolling 3 s mean peaks at {smooth.iloc[peak]:.2f} C at {cap['t_s'].iloc[peak]:.1f} s")

    run = (cap["over_temp"] != cap["over_temp"].shift()).cumsum()  # a new number at each change
    spans = (
        cap[cap["over_temp"]]
        .groupby(run[cap["over_temp"]])
        .agg(start=("t_s", "first"), end=("t_s", "last"), peak_c=("temperature_c", "max"))
    )
    spans["seconds"] = spans["end"] - spans["start"]
    print("\nover-temperature spans")
    print(spans.reset_index(drop=True).round(2))


if __name__ == "__main__":
    main()
