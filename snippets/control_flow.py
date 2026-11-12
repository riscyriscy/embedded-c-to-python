"""Control flow for a C programmer. Run: python3 control_flow.py"""

from collections.abc import Iterator


# ---- if / elif / else and the conditional expression ----
def classify_temp(celsius: float) -> str:
    if celsius < -40 or celsius > 125:
        return "out of range"
    elif celsius > 85:
        return "hot"
    return "ok"


for t in (-45.0, 25.0, 90.0):
    print(f"{t:6.1f} C -> {classify_temp(t)}")
state = "run" if classify_temp(25.0) == "ok" else "halt"  # like ?: in C
print(f"state={state}")

# ---- truthiness: zero and empty values are false, so test None explicitly ----
truthy_samples: tuple[object, ...] = (0, 0.0, "", [], {}, None, "0", [0])
print(", ".join(f"{value!r}->{bool(value)}" for value in truthy_samples))


def wait(timeout: float | None = None) -> str:
    if timeout is None:  # 'if not timeout' would treat 0 as "no timeout given"
        return "wait forever"
    return f"wait {timeout} s"


print(wait(0), "|", wait())

# ---- for, range, enumerate, zip: no index variable unless the loop needs one ----
readings = [512, 530, 498, 1023, 505]
for index, raw in enumerate(readings):
    if raw >= 1023:
        print(f"sample {index}: stuck at the rail, skipped")
        continue
print(f"range(10, 0, -3) -> {list(range(10, 0, -3))}")

rails = ["3V3", "1V8", "1V0"]
measured = [3.31, 1.79, 0.93]
limits = [(3.135, 3.465), (1.71, 1.89), (0.95, 1.05)]
for rail, volts, (low, high) in zip(rails, measured, limits, strict=True):
    print(f"{rail}: {volts:.2f} V {'ok' if low <= volts <= high else 'FAIL'}")  # chained compare


# ---- break, loop-else, while, walrus ----
def sync_search(stream: bytes, sync: int = 0xA5) -> int:
    for position, byte in enumerate(stream):
        if byte == sync:
            break
    else:  # runs only when the loop ended without break
        return -1
    return position


stream = bytes([0x00, 0x01, 0xA5, 0x10])
print(f"sync at {sync_search(stream)}, missing -> {sync_search(stream[:2])}")


def chunks(data: bytes, size: int) -> Iterator[bytes]:
    pos = 0
    while chunk := data[pos : pos + size]:  # assign and test in one expression
        yield chunk
        pos += size


print(list(chunks(b"ABCDEFG", 3)))

attempts = 0
while True:  # Python has no do/while: loop forever and break
    attempts += 1
    if attempts * attempts > 50:
        break
print(f"first n with n*n > 50: {attempts}")


# ---- match: a switch that also takes values apart ----
def run(command: str) -> str:
    match command.split():
        # isdigit() would also accept a superscript two, which int() rejects
        case ["set", "rate", rate] if rate.isascii() and rate.isdecimal():
            return f"rate={int(rate)} Hz"
        case ["set", name, text]:
            return f"cannot set {name!r} to {text!r}"
        case ["get", name]:
            return f"read {name}"
        case ["reset" | "reboot"]:
            return "restart"
        case []:
            return "empty line"
        case _:
            return "unknown command"


for line in (
    "set rate 10",
    "set rate abc",
    "set rate \u00b2",
    "set gain 3",
    "get temp",
    "reboot",
    "",
    "dance",
):
    print(f"{line!r:15} -> {run(line)}")

# ---- comprehensions and generator expressions ----
even_squares = [n * n for n in range(6) if n % 2 == 0]
total = sum(n * n for n in range(1000))  # generator: no list is built
print(even_squares, total, any(r >= 1023 for r in readings), all(r > 0 for r in readings))
