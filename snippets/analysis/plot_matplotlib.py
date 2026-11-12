"""matplotlib: plot a temperature log, an ADC histogram and a spectrum, headless.

Writes out/capture.png. The data is generated with a fixed seed, so the numbers are the
same on every run. Run: python3 plot_matplotlib.py
"""

import math
import random
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # no display needed: render to files only. Set this before importing pyplot
import matplotlib.pyplot as plt
import numpy as np

OUT = Path("out")
ALARM_C = 30.0


def main() -> None:
    OUT.mkdir(exist_ok=True)
    rng = random.Random(7)

    # 1. Temperature log: 60 s sampled at 10 Hz, a slow cycle plus noise
    t = np.arange(600) / 10
    temp = np.array([25 + 6 * math.sin(2 * math.pi * x / 40) + rng.gauss(0, 0.3) for x in t])

    # 2. 12-bit ADC codes of a constant 1.65 V input on a 3.3 V reference, with noise
    codes = np.clip(np.array([round(2048 + rng.gauss(0, 3)) for _ in range(2000)]), 0, 4095)

    # 3. Spectrum: 1 kHz and 3 kHz tones sampled at 48 kHz, 4800 samples (10 Hz per bin)
    fs, n = 48_000, 4800
    k = np.arange(n) / fs
    x = np.sin(2 * np.pi * 1000 * k) + 0.25 * np.sin(2 * np.pi * 3000 * k)
    spectrum = np.abs(np.fft.rfft(x * np.hanning(n))) / (n / 4)
    freqs = np.fft.rfftfreq(n, 1 / fs)
    s = spectrum[1:-1]
    is_peak = (s > spectrum[:-2]) & (s > spectrum[2:]) & (s > 0.1)  # local maxima above 0.1
    peaks = freqs[1:-1][is_peak]

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(6.5, 7.5), layout="constrained")
    ax1.plot(t, temp, linewidth=1, label="board temperature")
    ax1.axhline(ALARM_C, color="tab:red", linestyle="--", label=f"alarm {ALARM_C:.0f} °C")
    ax1.fill_between(t, ALARM_C, temp, where=temp > ALARM_C, color="tab:red", alpha=0.3)
    ax1.set(xlabel="time (s)", ylabel="temperature (°C)", title="Temperature log")
    ax1.legend(loc="lower right")

    ax2.hist(codes, bins=range(2030, 2068), color="tab:gray")
    ax2.axvline(codes.mean(), color="tab:blue")
    ax2.set(xlabel="ADC code", ylabel="count", title=f"ADC noise: sd {codes.std():.2f} codes")

    ax3.semilogy(freqs[:800], spectrum[:800] + 1e-6)
    ax3.set(xlabel="frequency (Hz)", ylabel="amplitude", title="Spectrum (Hann window)")
    ax3.annotate("1 kHz", (1000, 1.0), xytext=(1400, 0.6), arrowprops={"arrowstyle": "->"})

    fig.savefig(OUT / "capture.png", dpi=110)
    plt.close(fig)  # free the figure: a long-running script otherwise leaks memory

    print(
        f"max {temp.max():.2f} C at {t[temp.argmax()]:.1f} s, above alarm: {(temp > ALARM_C).sum()} samples"
    )
    print(
        f"ADC mean {codes.mean():.2f}, sd {codes.std():.2f}, codes {codes.min()} to {codes.max()}"
    )
    print("spectrum peaks (Hz):", sorted(float(p) for p in peaks))
    png = OUT / "capture.png"
    print(png, png.stat().st_size > 10_000, plt.get_backend())


if __name__ == "__main__":
    main()
