"""Hypothesis finds and shrinks a bug: a COBS encoder with an off-by-one at the block limit.

The correct limit is 0xFF (a block of 254 data bytes). The copy below uses 0xFE, so a run of
253 non-zero bytes is cut early, and the decoder, which is correct, puts a zero after it.
Run: python3 buggy_cobs_demo.py   (needs the frametool package: uv sync)
"""

import random

from frametool import cobs
from hypothesis import given, settings
from hypothesis import strategies as st


def encode_buggy(src: bytes) -> bytes:
    out = bytearray(b"\x00")
    code_index, code = 0, 1
    for b in src:
        if b == 0:
            out[code_index] = code
            code_index, code = len(out), 1
            out.append(0)
            continue
        out.append(b)
        code += 1
        if code == 0xFE:  # BUG: must be 0xFF
            out[code_index] = code
            code_index, code = len(out), 1
            out.append(0)
    out[code_index] = code
    return bytes(out)


failures: list[bytes] = []
seen: list[bytes] = []  # every input that the plain-bytes strategy generated


def longest_run(data: bytes) -> int:
    """The longest run of non-zero bytes."""
    best = current = 0
    for b in data:
        current = current + 1 if b else 0
        best = max(best, current)
    return best


def check(data: bytes) -> None:
    try:
        assert cobs.decode(encode_buggy(data)) == data
    except AssertionError:
        failures.append(data)  # the last one recorded is the shrunk example
        raise


# Strategy 1: arbitrary bytes. Hypothesis prefers short inputs, so a run of 253 is never reached.
@settings(max_examples=300, derandomize=True, deadline=None, database=None)
@given(st.binary(max_size=600))
def with_plain_bytes(data: bytes) -> None:
    seen.append(data)
    check(data)


# Strategy 2: describe the structure that matters. Runs of one repeated byte, of lengths
# around the block limit, mixed with short random pieces.
runs = st.builds(lambda n, b: bytes([b]) * n, st.integers(250, 256), st.integers(1, 255))
structured = st.lists(st.one_of(st.binary(max_size=4), runs), max_size=3).map(b"".join)


@settings(max_examples=300, derandomize=True, deadline=None, database=None)
@given(structured)
def with_runs(data: bytes) -> None:
    check(data)


def main() -> None:
    with_plain_bytes()
    print("plain bytes: no failure found in 300 examples")
    print(
        "plain bytes: longest input",
        max(len(s) for s in seen),
        "bytes, longest non-zero run",
        max(longest_run(s) for s in seen),
    )
    rng = random.Random(1)
    with_run = sum(longest_run(rng.randbytes(600)) >= 253 for _ in range(1000))
    print(
        "uniform random 600-byte strings with a non-zero run of 253 or more:", with_run, "of 1000"
    )
    try:
        with_runs()
    except AssertionError:
        print("with runs: Hypothesis found a failing example")
        minimal = failures[-1]
        print(
            "smallest failing input:", len(minimal), "bytes, distinct values", sorted(set(minimal))
        )
        print("correct encoder round trip:", cobs.decode(cobs.encode(minimal)) == minimal)
        print("buggy encoder round trip:", cobs.decode(encode_buggy(minimal)) == minimal)


if __name__ == "__main__":
    main()
