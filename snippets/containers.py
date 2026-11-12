"""Built-in containers with firmware-flavoured data. Run: python3 containers.py"""

from bisect import bisect_left
from collections import Counter, defaultdict, deque

# ---- list: ordered, mutable. A capture of ADC samples ----
samples = [512, 530, 498, 1023, 505, 0, 517, 522]
valid = [s for s in samples if 0 < s < 1023]  # list comprehension: filter out rail-stuck readings
print(f"valid={valid} min={min(valid)} max={max(valid)} mean={sum(valid) / len(valid):.1f}")
print(f"first three={samples[:3]} last two={samples[-2:]} every other={samples[::2]}")

# ---- tuple: fixed-size, immutable record. Unpacking and comparison ----
fw_running = (1, 10, 0)
fw_available = (1, 9, 3)
major, minor, patch = fw_running  # unpacking, like reading struct fields
print(f"running {major}.{minor}.{patch}, update needed: {fw_available > fw_running}")
as_strings = "1.9.3" > "1.10.0"  # noqa: PLR0133 (deliberately comparing two constants)
print(f"compare as strings instead: '1.9.3' > '1.10.0' is {as_strings} (wrong!)")

# ---- dict: key -> value lookup. A register map and an error-code table ----
REGS = {"CTRL": 0x00, "STATUS": 0x04, "DATA": 0x08, "IRQ_EN": 0x0C}
ERRORS = {0x01: "overtemp", 0x02: "undervoltage", 0x04: "sensor fault"}
by_addr = {addr: name for name, addr in REGS.items()}  # dict comprehension: invert the map
print(f"STATUS at {REGS['STATUS']:#04x}; 0x08 is {by_addr[0x08]}")
print(f"code 0x04 -> {ERRORS.get(0x04, 'unknown')}, code 0x80 -> {ERRORS.get(0x80, 'unknown')}")
for name, addr in sorted(REGS.items(), key=lambda kv: kv[1], reverse=True):  # sort by address
    print(f"  {addr:#04x} {name}")

# ---- set: membership and set algebra. Board bring-up checks ----
required = {"UART0", "SPI1", "I2C0", "GPIO"}
detected = {"UART0", "I2C0", "GPIO", "USB"}
print(
    f"missing={sorted(required - detected)} unexpected={sorted(detected - required)} "
    f"ok={sorted(required & detected)}"
)
pins = {"UART0_TX": "PA9", "UART0_RX": "PA10", "SPI1_SCK": "PA5", "LED": "PA5"}
clashes = [pin for pin, uses in Counter(pins.values()).items() if uses > 1]  # Counter: see below
print(f"pin clashes: {clashes}")

# ---- deque(maxlen): a ring buffer that discards the oldest entry ----
last5: deque[int] = deque(maxlen=5)
for s in samples:
    last5.append(s)
print(f"last five samples: {list(last5)}")

# ---- Counter: histogram of events from a log ----
log = ["CRC", "TIMEOUT", "CRC", "OK", "OK", "CRC", "OK", "NAK", "OK", "OK"]
errors = Counter(e for e in log if e != "OK")
print(f"error histogram: {dict(errors)}; most common: {errors.most_common(1)[0]}")

# ---- defaultdict(list): group records by key without 'if key not in d' boilerplate ----
frames = [(0x10, 1), (0x01, 2), (0x10, 3), (0x20, 4), (0x10, 5)]  # (type, seq)
by_type: defaultdict[int, list[int]] = defaultdict(list)
for ftype, seq in frames:
    by_type[ftype].append(seq)
print("sequence numbers by type:", {f"{k:#04x}": v for k, v in by_type.items()})

# ---- bisect: interpolate a thermistor calibration table (ADC counts -> degC) ----
ADC = [180, 310, 512, 720, 860]  # must be sorted
TEMP = [80.0, 50.0, 25.0, 5.0, -10.0]


def adc_to_temp(counts: int) -> float:
    if not ADC[0] <= counts <= ADC[-1]:  # outside the table the line would extrapolate
        raise ValueError(f"ADC {counts} is outside the table {ADC[0]} to {ADC[-1]}")
    i = max(bisect_left(ADC, counts), 1)  # binary search; the first interval also takes ADC[0]
    x0, x1, y0, y1 = ADC[i - 1], ADC[i], TEMP[i - 1], TEMP[i]
    return y0 + (y1 - y0) * (counts - x0) / (x1 - x0)


print(f"ADC 512 -> {adc_to_temp(512):.1f} C, ADC 600 -> {adc_to_temp(600):.1f} C")
try:
    adc_to_temp(0)  # a shorted or open thermistor reads outside the table
except ValueError as e:
    print(e)
