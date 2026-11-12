"""Reading a traceback. Run: python3 traceback_demo.py  (it ends with an uncaught error, exit status 1)"""


class ConfigError(Exception):
    pass


def read_register(regs: dict[str, int], name: str) -> int:
    return regs[name]


def read_field(regs: dict[str, int], name: str, shift: int, width: int) -> int:
    value = read_register(regs, name)
    return (value >> shift) & ((1 << width) - 1)


def configure(regs: dict[str, int]) -> int:
    try:
        return read_field(regs, "CTRL", 4, 3)
    except KeyError as exc:
        raise ConfigError(f"register {exc.args[0]} is missing") from exc


configure({"STATUS": 0x81})
