# /// script
# requires-python = ">=3.12"
# dependencies = ["pyserial>=3.5,<4"]
# ///
"""Production-test step on a loop:// port. Run: uv run board_check.py"""

import serial

LIMITS = {"VBAT": (3.0, 4.2), "TEMP": (-10.0, 60.0)}


def check(name: str, value: float) -> bool:
    low, high = LIMITS[name]
    ok = low <= value <= high
    print(f"{name:<5}{value:>7.2f}  {'PASS' if ok else 'FAIL'}  ({low} to {high})")
    return ok


def main() -> int:
    # loop:// echoes what is written, so the script needs no hardware
    with serial.serial_for_url("loop://", timeout=0.2) as port:
        results = []
        for name, reading in (("VBAT", 3.71), ("TEMP", 24.5)):
            port.write(f"{reading}\n".encode("ascii"))
            results.append(check(name, float(port.readline().decode("ascii"))))
    print("pyserial", serial.__version__)
    print("RESULT", "PASS" if all(results) else "FAIL")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
