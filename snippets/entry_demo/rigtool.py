"""Average a number of ADC readings. Run it, run it with -m, or import it.

Run:   python rigtool.py 3          (or: python -m rigtool 3)
"""

import sys

print(f"rigtool: this file is running with __name__ = {__name__!r}")


def average_mv(readings: list[int]) -> float:
    return sum(readings) / len(readings)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: rigtool COUNT", file=sys.stderr)
        return 2  # like `return 2;` from main() in C
    count = int(argv[1])
    mean = average_mv([3300 + n for n in range(count)])
    print(f"average of {count} readings: {mean} mV")
    return 0


# True only when this file is started, not when it is imported.
if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
