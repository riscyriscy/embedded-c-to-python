"""C habit versus Python idiom: statistics over ADC samples. Run: python3 idiom_stats.py"""

import statistics

# 10-bit counts; 0 and 1023 are rail hits
SAMPLES = [512, 530, 498, 1023, 505, 0, 520, 515, 1023, 497]


def stats_c_style(samples: list[int]) -> tuple[int, int, float, int, int]:
    """Index loop, running totals and sentinel start values."""
    lo = 1 << 30
    hi = -(1 << 30)
    total = 0
    peak_index = 0
    clipped = 0
    for i in range(len(samples)):
        v = samples[i]
        total += v
        if v < lo:
            lo = v
        if v > hi:
            hi = v
            peak_index = i
        if v == 0 or v == 1023:
            clipped += 1
    return lo, hi, total / len(samples), peak_index, clipped


def stats_pythonic(samples: list[int]) -> tuple[int, int, float, int, int]:
    """Built-ins that name the intent."""
    peak_index = samples.index(max(samples))
    clipped = sum(v in (0, 1023) for v in samples)  # True counts as 1
    return min(samples), max(samples), statistics.fmean(samples), peak_index, clipped


def moving_average_c_style(samples: list[int], n: int) -> list[float]:
    out = []
    for i in range(len(samples) - n + 1):
        acc = 0
        for j in range(n):
            acc += samples[i + j]
        out.append(acc / n)
    return out


def moving_average_pythonic(samples: list[int], n: int) -> list[float]:
    return [sum(samples[i : i + n]) / n for i in range(len(samples) - n + 1)]


a, b = stats_c_style(SAMPLES), stats_pythonic(SAMPLES)
print("min, max, mean, peak index, clipped:", a)
print("same result from the built-ins:", a == b)
print("moving average of 4:", [round(v, 1) for v in moving_average_pythonic(SAMPLES, 4)])
print(
    "same moving average:",
    moving_average_c_style(SAMPLES, 4) == moving_average_pythonic(SAMPLES, 4),
)
