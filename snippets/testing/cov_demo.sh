#!/usr/bin/env bash
# Line and branch coverage with pytest-cov, a coverage gate, and tests that close gaps.
# Run: bash cov_demo.sh   (needs uv, access to PyPI, and limitcheck/ beside it)
set -u
here=$(cd "$(dirname "$0")" && pwd)
demo=${DEMO_DIR:-/tmp/cov_demo}
rm -rf "$demo" && mkdir -p "$demo" && cd "$demo"
export UV_CACHE_DIR="$demo/cache"
cp -r "$here/limitcheck" . && cd limitcheck
uv sync --quiet

echo "== 1. line and branch coverage, missing lines and branches listed"
uv run pytest -q -p no:cacheprovider --cov=limitcheck --cov-branch \
    --cov-report=term-missing

echo "== 2. without --cov-branch the report counts lines only"
uv run pytest -q -p no:cacheprovider --cov=limitcheck --cov-report=term-missing \
    | grep -E '^(limits|src/limitcheck/limits|TOTAL)'

echo "== 3. the same run as a gate: below 95 percent the exit code is not 0"
uv run pytest -q -p no:cacheprovider --cov=limitcheck --cov-branch \
    --cov-fail-under=95 > gate.txt 2>&1
echo "exit code $?"
tail -3 gate.txt

echo "== 4. two more tests, one for each gap"
cat > tests/test_gaps.py <<'PY'
"""Tests for the two gaps. Run: uv run pytest -q"""

from limitcheck.limits import Limit, classify, verdict


def test_nan_is_its_own_class() -> None:
    assert classify(float("nan"), Limit(3.0, 4.2)) == "NAN"


def test_unknown_channel_is_skipped() -> None:
    assert verdict(["SPARE=99"], {"VBAT": Limit(3.0, 4.2)})
PY
uv run pytest -q -p no:cacheprovider --cov=limitcheck --cov-branch \
    --cov-fail-under=100 --cov-report=term-missing
echo "exit code $?"
