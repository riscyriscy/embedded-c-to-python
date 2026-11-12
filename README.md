# From Embedded C to Python: companion code

Source code for Book 1 of 2, "From Embedded C to Python" (C. Paul Gordon, October 2026). Every listing
in the book comes from this repository, and every example was run as written. The companion volume,
"Python Beside C", has its own repository (`python-beside-c`) with the code that calls C or is
called from C.

Eleven sections were removed from the original single volume. Two of them, the debug-probe and the hardware-test
sections, went back into Book 1, Phase 7. The other nine are kept as reserve material, and their code stays in this
repository and still runs. The rows below that say "reserve" are that code, so the book
does not show it.

## Layout

| Path | Book phase | What it is |
|---|---|---|
| `snippets/interpreter/` | 1 | The interactive prompt and the debugger: `repl_session.txt` and `repl_replay.py` (replays a console session with its prompts), `traceback_demo.py` (a chained exception), `pdb_demo.py` with `pty_drive.py` (drives a real pdb session through a pseudo-terminal) `test_fail.py` (`pytest --pdb`), `hang_demo.py` with `hang_signal.sh` and `hang_attach.sh` (a hung main thread: `faulthandler` watchdog, a `SIGUSR1` dump and `pdb -p` on Python 3.14), and `warn_demo.py` with `legacy_clock.py` (`-X dev` and `-W error::DeprecationWarning`) |
| `frametool-py/.vscode/` | 1 | The four editor files of Phase 1, "Editors": `settings.json`, `extensions.json`, `tasks.json` and `launch.json` for Visual Studio Code and VSCodium |
| `snippets/editor/vscode-config.sh` | 1 | Copies the user files of the editor to and from a repository and installs the listed extensions (`capture` and `apply`) |
| `snippets/tour.py` | 1 | Python for a C programmer: integers, bytes, struct, pattern matching |
| `snippets/syntax_summary.py` | 1 | Checks the claims behind the syntax tables of the book (basic types and literals, C statements next to their Python forms) and the list, tuple, dict and set operations: 59 checks, prints one line per table |
| `snippets/or_defaults.py` | 1 | Three ways to supply a default (`or`, `get(key, default)`, `is None`) on a retries setting where 0 is valid, and what `or` and `and` return |
| `snippets/entry_demo/` | 1 | `rigtool.py`, `use_rigtool.py`, `pkgtool/__main__.py` and `run.sh`: `main()`, the `__name__ == "__main__"` guard, `python file.py` against `python -m`, importing, and the exit status of each run |
| `snippets/venv/` | 1, 5 | Virtual environments: `venv_demo.sh` (venv, pip freeze, rebuild from requirements.txt), `uv_demo.sh` (uv venv, pip compile and sync, hash checking, uv.lock, uv export), `venv_info.py`; reserve: `uv_script_demo.sh` with `board_check.py` (PEP 723 script), `uv_dev_demo.sh` (dependency groups, `.python-version`) |
| `snippets/model/` | 1 | `c_facts.c` and `py_facts.py`: sizes, integer division and wrap-around in C against Python, side by side |
| `snippets/annotations/` | 1 | `annotations_demo.py` (most forms of annotation syntax in the book, and what Python does with them) and `forward_ref.py` (a forward reference: a `NameError` on 3.12, fine on 3.14) |
| `snippets/control_flow.py`, `text_strings.py`, `bits_format.py`, `identity.py`, `dictionaries.py`, `exceptions_demo.py`, `basic_structures.py`, `exception_cost.py` | 1 (continued) | Control flow, strings, number formatting and bit manipulation, `is` versus `==`, dictionaries, exceptions, basic data structures; a timing of `try`/`except` against an `in` check |
| `snippets/keyword_args.py`, `kwargs_forwarding.py`, `kwargs_unpack_bad.py` | 1 (continued) | Keyword arguments, then `**kwargs` forwarded to a known signature, the typo it hides, pop-and-reject, `Unpack[TypedDict]` (PEP 692) and a `ParamSpec` retry decorator; `kwargs_unpack_bad.py` is the file mypy rejects on purpose |
| `snippets/zip_usage.py` | 1 (continued) | `zip` on firmware data: parallel lists, `strict=True`, `zip_longest`, `dict(zip(...))`, naming struct fields, `zip(*rows)`, `pairwise`, `batched`, `max(zip(...))`, one-pass iterators, and the item lost from a first-position iterator |
| `snippets/idioms/` | 1 (continued) | Seven problems solved the C way and the Python way, each script checking that both agree: statistics, register lookup, key=value parsing, header pack and unpack, CRC-16, errors and cleanup, a state machine |
| `snippets/numeric/numeric_traps.py` | 1 (continued) | Wrapping, casts, rounding, NaN, `int(s, 0)` and ASCII-only parsing, `float` parsing, `splitlines` and lone `\r`, `UnicodeDecodeError` |
| `snippets/numeric/` (the other files) | reserve | `struct_sizes.py` and `struct_tricks.py`, `late_binding.py`, `encoding_demo.py`, `pipe_parent.py` with `pipe_child.py` (when output reaches a pipe), `shadow_demo.py`, `exit_status.py` |
| `snippets/construct_demo.py` | 2 | construct: the frametool frame described once, parsed and built, checked against the struct code, including a 12-byte payload that `c.Terminated` rejects |
| `snippets/stream_parser.py` | 2 | A `StreamParser` that accumulates reads in a `bytearray`, skips noise to the sync byte, rejects a false header by length limit and CRC, and resyncs one byte at a time; it gives the same frames for one read, one byte per read and 200 random splits |
| `snippets/protobuf_demo/` | 2 | The telemetry record as a packed struct, a construct `Struct` and a protobuf message: sizes, a reader that meets a new field, zero against absent (`optional` and `HasField`), and decode speed. `telemetry_pb2.py` is generated from `telemetry.proto` by protoc 7.35.1 and needs `protobuf>=7.35.1` at run time |
| `snippets/containers.py`, `classes.py`, `dispatch.py` | 3 | Data structures, classes, a message registry and dispatch table (validation in `__post_init__`); `adc_to_temp()` raises outside the table |
| `snippets/files/` | 3 (continued) | UART log scanner, production-test report (CSV/TOML to CSV/JSON/Markdown; a `nan` or blank value fails, and `limits.toml` has a minimum temperature), Intel HEX tools |
| `snippets/concurrency/` | 4 | `threads_demo.py` (a data race, a bounded queue, the asyncio bridge, a stop flag, a timer), `procs_demo.py` (start methods, pickling, the main guard) and `noguard_demo.py` (the guard left out), and `rt_hints.py` (`sched_setaffinity`, `mlockall` through `ctypes` with its page-fault effect and its refusal without privilege, and `tracemalloc`; Linux, run as root); reserve: `shutdown_signals.py` (what SIGINT, SIGTERM and SIGKILL do to a child that holds a supply on, with and without a SIGTERM handler) and `wake_jitter.py` (wake-up lateness of a SCHED_FIFO thread with and without a busy thread, a shorter switch interval and a second process; Linux, run as root) |
| `frametool-py/` | 5, 6 | The `frametool` package as pure Python: COBS/CRC framing, a `src` layout built with `uv_build` into a `py3-none-any` wheel, a `frametool` command from `[project.scripts]`, a `serial` extra, a `dev` dependency group and a pytest suite of 26 tests including the Hypothesis property tests (with `@example` cases at the 253 to 255 byte boundary). Book 2 adds a C extension to this package |
| `snippets/lint/` | 6 | `lint_demo.py`, a deliberately flawed file for comparing ruff, flake8, pylint, black, isort, bandit, vulture, mypy and pyright, and a starting `pyproject.toml` for ruff and mypy |
| `snippets/testing/buggy_cobs_demo.py` | 6 | Hypothesis: a bug that Hypothesis's default byte strategy never reaches and a structured strategy finds |
| `snippets/testing/` (the other files) | reserve | `limitcheck/` (a package with tests and `ci.sh`), `ci_lock_demo.sh`, `ci_run_demo.sh`, `cov_demo.sh`, `mypy_gate.sh`, `frametool_dev.sh`, and `port_scan.py` (lists the serial ports and reads one line from the first) |
| `snippets/hardware/` | 7 | pyserial (`serial_demo.py`), pyusb (`usb_demo.py`) and python-can (`can_demo.py`), each runnable without hardware (`serial_demo.py` also shows an unplug on a pseudo-terminal and converts `termios.error` to `SerialException`, and a late reply after a timeout that the next query takes for its own answer); `multi_dut.py` (pick one of several identical adapters by vendor ID, product ID and serial number or USB location; one thread per DUT); `serial_edges.py` (asserts `read_until`, `readline` on binary data, `inter_byte_timeout`, `write_timeout`, `exclusive` and the RS-485 ioctl result on a pseudo-terminal) and `can_edges.py` (asserts `bus.state`, `shutdown()` and `BitTiming` on the virtual bus); `dbc/` (`engine.dbc`, `dbc_demo.py` with cantools: encode, decode, range errors and a decode of what python-can receives; `dbc_c_check.c`, which uses the C code from `python -m cantools generate_c_source`); `resilient_link.py` and `test_resilient_link.py`, a retry, backoff and reconnect wrapper with 7 tests that need no hardware; `peripherals.py` and `test_peripherals.py` (I2C with smbus2, SPI with spidev, a GPIO edge with libgpiod 2.x and a `mmap` plus `ctypes.Structure` register block, each against a fake; 6 tests, the two smbus2 tests skip when smbus2 is absent) |
| `snippets/analysis/` | 7 | matplotlib (`plot_matplotlib.py`, writes a PNG), plotly (`plot_plotly.py`, writes an HTML file) and pandas (`capture_pandas.py`: parse a UART log, find gaps, window counts, over-temperature spans) |
| `snippets/extras/host_monitor.py` | 7 | psutil: host checks, child-process monitoring, stopping a process tree (`kill_tree()` returns the exit statuses from `wait_procs`) |
| `snippets/extras/logging_demo.py`, `test_logging_demo.py` | 8 | Logging with a run context, a rotating file, JSON lines, a bounded queue for threads that drops and counts records, UTC time stamps, a console formatter that hides the traceback whatever handler formats first, and 7 caplog tests |
| `snippets/extras/practices.py`, `fetch_status.py` | 8 | Habits for host tools, with an `atomic_write()` that keeps the file mode, syncs the file and the directory and removes its temporary file on failure; a PEP 723 single-file script |
| `snippets/hil_pytest/` | 7 | A pytest suite for a fake TLM-100 device: `--dut` option, a registered `hardware` marker, a yield fixture that resets the device, `pytest-timeout`; `demo_failures.py` and `demo_typo.py` fail on purpose |
| `snippets/probe_scripting/` | 7 | `fw_probe.c` and `fw_build.sh` (an ELF built with arm-none-eabi-gcc), `elf_symbols.py` (read a global by name through a `Probe` protocol), `pyocd_adapter.py`, `rtt_logging.py`, `openocd_tcl.py` (OpenOCD's Tcl port) |

## Requirements

- Python 3.12 or later (examples were run on 3.14 and 3.12)
- [uv](https://docs.astral.sh/uv/)
- A C compiler (only for `snippets/model/c_facts.c` and `snippets/probe_scripting/`), arm-none-eabi-gcc and OpenOCD (optional, reserve material)

Nothing in this repository needs CMake or a C++ compiler. The code that does is in `python-beside-c`.

## Quick start

```bash
# The frametool package: pure Python, built with uv_build
cd frametool-py
uv sync
uv run pytest -q                        # includes the Hypothesis property tests
uv run ruff check . && uv run mypy src tests
uv run python -m frametool              # live demo for 3 seconds
uv build --out-dir dist                 # sdist and a py3-none-any wheel

# Everything else
cd ../snippets
uv sync
uv run python tour.py
uv run python syntax_summary.py
uv run python or_defaults.py
uv run python zip_usage.py
bash entry_demo/run.sh                               # PYTHON=python3.12 bash entry_demo/run.sh picks an interpreter
uv run python annotations/annotations_demo.py && uv run python annotations/forward_ref.py   # the second fails on 3.12 on purpose
uv run python numeric/numeric_traps.py
(cd numeric && for f in struct_sizes struct_tricks late_binding pipe_parent shadow_demo exit_status; do uv run python $f.py; done)   # reserve
(cd numeric && LC_ALL=C PYTHONCOERCECLOCALE=0 uv run python -X utf8=0 encoding_demo.py)   # reserve
(cd concurrency && uv run python threads_demo.py && uv run python procs_demo.py && uv run python noguard_demo.py)
(cd concurrency && sudo uv run python rt_hints.py)   # Linux; the lock needs root or CAP_IPC_LOCK
(cd hil_pytest && uv run pytest -q --dut fake && uv run pytest -q)   # reserve; without --dut the hardware tests are skipped
(cd probe_scripting && sh fw_build.sh && uv run python elf_symbols.py && uv run python pyocd_adapter.py && uv run python rtt_logging.py && uv run python openocd_tcl.py)   # reserve
(cd testing && bash ci_lock_demo.sh && bash cov_demo.sh && bash mypy_gate.sh)   # reserve; needs network access to PyPI
bash venv/uv_script_demo.sh && bash venv/uv_dev_demo.sh   # reserve
uv run python control_flow.py && uv run python text_strings.py && uv run python bits_format.py && uv run python identity.py && uv run python dictionaries.py
uv run python exceptions_demo.py && uv run python basic_structures.py && uv run python exception_cost.py
uv run python keyword_args.py && uv run python kwargs_forwarding.py
uv run mypy kwargs_unpack_bad.py                     # fails on purpose: mypy rejects the misspelt keyword
uv run python construct_demo.py && uv run python testing/buggy_cobs_demo.py && uv run python stream_parser.py
uv run python protobuf_demo/protobuf_compare.py
uv run python containers.py && uv run python classes.py && uv run python dispatch.py
uv run python model/py_facts.py && cc -O0 -o /tmp/c_facts model/c_facts.c && /tmp/c_facts
for f in idioms/idiom_*.py; do uv run python $f; done
bash venv/venv_demo.sh && bash venv/uv_demo.sh        # need network access to PyPI; write to /tmp

cd interpreter                           # the prompt, tracebacks and pdb
uv run python repl_replay.py repl_session.txt
uv run python hang_demo.py --watchdog     # exits after 2 s with the stacks; --signal and --poll are the other modes
sh hang_signal.sh                         # SIGUSR1 dumps the stacks of a running tool
PY=python3.14 sh hang_attach.sh           # pdb -p, Python 3.14 only
uv run python warn_demo.py && python -X dev warn_demo.py && python -W error::DeprecationWarning legacy_clock.py
uv run python traceback_demo.py          # exits with status 1 on purpose
uv run pytest -q test_fail.py            # fails on purpose; add --pdb to stop at the failure
uv run python pty_drive.py "(Pdb) " "l;p total;p frame;bt;up;p frame;down;n;p (-total) & 0xFF;c" python pdb_demo.py   # the session in the book
cd ..

cd hardware                              # no devices needed: pty, fake USB device, virtual CAN bus
uv run python serial_demo.py && uv run python usb_demo.py && uv run python can_demo.py && uv run python serial_edges.py && uv run python can_edges.py
uv run python multi_dut.py && uv run python resilient_link.py && uv run pytest -q test_resilient_link.py
uv run python peripherals.py && uv run pytest -q test_peripherals.py
(cd dbc && uv run --with cantools --with python-can python dbc_demo.py && uv run --with cantools python -m cantools generate_c_source -o gen engine.dbc && gcc -Wall -Wextra -Werror -Igen -o c_check dbc_c_check.c gen/engine.c && ./c_check)
cd ../analysis                           # these write ./out
uv run python plot_matplotlib.py && uv run python plot_plotly.py && uv run python capture_pandas.py   # needs pandas
cd ../lint
uvx ruff check lint_demo.py              # also: uvx flake8, pylint, bandit, vulture, black --check, isort --check
cd ..

cd files                                 # these read ./data and write ./out
uv run python logscan.py data/uart.log
uv run python testreport.py
uv run python ihex.py
cd ..

cd extras
uv run python practices.py
uv run python host_monitor.py
uv run python logging_demo.py && uv run pytest -q test_logging_demo.py
uv run fetch_status.py                   # PEP 723: uv reads the dependencies from the file
```

## Notes

- `frametool-py/uv.lock` and `snippets/uv.lock` pin the exact versions the examples were run with
  (Python 3.14, among others).
- Code quality gates used for the book: `ruff check`, `ruff format --check` and `mypy --strict`.
- Licence: MIT. See `LICENSE`.
