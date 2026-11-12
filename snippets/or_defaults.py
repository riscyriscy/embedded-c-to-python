"""Three ways to supply a default, and what `or` and `and` return.

Run:   python or_defaults.py
"""

Config = dict[str, int | None]


def retries_or(cfg: Config) -> int:
    return cfg.get("retries") or 3


def retries_get(cfg: Config) -> int | None:
    return cfg.get("retries", 3)


def retries_is_none(cfg: Config) -> int:
    value = cfg.get("retries")
    return 3 if value is None else value


CASES: list[Config] = [{}, {"retries": 5}, {"retries": 0}, {"retries": None}]

print(f"{'config':20} {'or':>4} {'get':>5} {'is None':>8}")
for cfg in CASES:
    print(f"{cfg!s:20} {retries_or(cfg):>4} {retries_get(cfg)!s:>5} {retries_is_none(cfg):>8}")


# `or` and `and` return one of their operands, not True or False.
def show(label: str, value: object) -> None:
    print(f"{label:28} -> {value}")


zero = 0
name = ""
items: list[int] = []
print()
show("0 or 3", zero or 3)
show('"" or "unknown"', name or "unknown")
show("3 and 7", 3 and 7)
show("items and items[0]", items and items[0])
show("items[0] if items else None", items[0] if items else None)
