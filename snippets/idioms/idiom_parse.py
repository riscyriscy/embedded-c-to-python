"""C habit versus Python idiom: parsing key=value settings. Run: python3 idiom_parse.py"""

from collections.abc import Callable

CONFIG = """# rig.cfg
port = /dev/ttyUSB0
baud=115200

  timeout = 2.5
retries = 0x03
this line has no equals sign
"""


def parse_c_style(text: str) -> tuple[dict[str, str], int]:
    """Walk the text one character at a time, as strchr and pointer arithmetic would."""
    result: dict[str, str] = {}
    errors = 0
    pos = 0
    n = len(text)
    while pos < n:
        end = pos
        while end < n and text[end] != "\n":
            end += 1
        start, stop = pos, end
        pos = end + 1
        while start < stop and text[start] in " \t":
            start += 1
        if start == stop or text[start] == "#":
            continue
        eq = -1
        k = start
        while k < stop:
            if text[k] == "=":
                eq = k
                break
            k += 1
        if eq < 0:
            errors += 1
            continue
        key_end = eq
        while key_end > start and text[key_end - 1] in " \t":
            key_end -= 1
        val_start = eq + 1
        while val_start < stop and text[val_start] in " \t":
            val_start += 1
        val_end = stop
        while val_end > val_start and text[val_end - 1] in " \t\r":
            val_end -= 1
        result[text[start:key_end]] = text[val_start:val_end]
    return result, errors


def parse_pythonic(text: str) -> tuple[dict[str, str], list[int]]:
    settings: dict[str, str] = {}
    bad_lines: list[int] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")  # sep is "" when there is no "="
        if not sep:
            bad_lines.append(number)  # which lines, not just how many
            continue
        settings[key.strip()] = value.strip()
    return settings, bad_lines


CONVERTERS: dict[str, Callable[[str], object]] = {
    "baud": int,
    "timeout": float,
    "retries": lambda v: int(v, 0),
}

c_settings, c_errors = parse_c_style(CONFIG)
py_settings, py_bad = parse_pythonic(CONFIG)
print("C style:      ", c_settings, "bad lines:", c_errors)
print("Pythonic:     ", py_settings, "bad lines:", py_bad)
print("same settings:", c_settings == py_settings)
print("typed values: ", {k: CONVERTERS.get(k, str)(v) for k, v in py_settings.items()})
