"""plotly: an interactive temperature plot as one self-contained HTML file.

Writes out/telemetry.html. Open it in a browser: hover shows values, the mouse wheel zooms,
and the range slider selects a time window. The data uses a fixed seed. Run: python3 plot_plotly.py
"""

import math
import random
from pathlib import Path

import plotly.graph_objects as go  # type: ignore[import-untyped]  # plotly has no type stubs
from plotly.subplots import make_subplots  # type: ignore[import-untyped]

OUT = Path("out")
ALARM_C = 30.0


def main() -> None:
    OUT.mkdir(exist_ok=True)
    rng = random.Random(7)
    t = [i / 10 for i in range(600)]  # 60 s at 10 Hz
    temp = [25 + 6 * math.sin(2 * math.pi * x / 40) + rng.gauss(0, 0.3) for x in t]
    rail = [3.30 + rng.gauss(0, 0.01) - (0.2 if 20 < x < 25 else 0) for x in t]  # a brown-out dip

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=("Board temperature", "3V3 rail"),
    )
    fig.add_trace(
        go.Scatter(
            x=t,
            y=temp,
            name="temperature",
            mode="lines",
            hovertemplate="%{x:.1f} s: %{y:.2f} °C<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_hline(
        y=ALARM_C, line={"color": "red", "dash": "dash"}, annotation_text="alarm", row=1, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=t,
            y=rail,
            name="3V3",
            mode="lines",
            hovertemplate="%{x:.1f} s: %{y:.3f} V<extra></extra>",
        ),
        row=2,
        col=1,
    )
    fig.add_hrect(
        y0=3.135, y1=3.0, line_width=0, fillcolor="red", opacity=0.15, row=2, col=1
    )  # below -5 %
    fig.update_xaxes(
        title_text="time (s)", rangeslider={"visible": True, "thickness": 0.05}, row=2, col=1
    )
    fig.update_yaxes(title_text="°C", row=1, col=1)
    fig.update_yaxes(title_text="V", range=[3.0, 3.4], row=2, col=1)
    fig.update_layout(
        title="Telemetry capture", height=600, hovermode="x unified", showlegend=False
    )

    # include_plotlyjs=True embeds the JavaScript library: a file of about 4.85 MB that works
    # offline.
    # "cdn" makes a file of about 37 KB that needs internet access when it is opened.
    fig.write_html(OUT / "telemetry.html", include_plotlyjs=True)
    fig.write_html(OUT / "telemetry_cdn.html", include_plotlyjs="cdn")

    print("traces:", [trace.name for trace in fig.data], "points per trace:", len(fig.data[0].x))
    print(
        f"max {max(temp):.2f} C, rail minimum {min(rail):.3f} V, below 3.135 V: {sum(v < 3.135 for v in rail)} samples"
    )
    full, cdn = (OUT / "telemetry.html").stat().st_size, (OUT / "telemetry_cdn.html").stat().st_size
    print(f"offline file over 3 MB: {full > 3_000_000}, cdn file under 100 KB: {cdn < 100_000}")


if __name__ == "__main__":
    main()
