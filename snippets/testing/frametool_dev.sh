#!/usr/bin/env bash
# Add types-pyserial to the dev group of a COPY of frametool-py; test and type-check.
# Run: bash frametool_dev.sh ../../frametool-py   (needs uv and access to PyPI)
set -eu
src=$(realpath "${1:?path of frametool-py}")
demo=${DEMO_DIR:-/tmp/frametool_dev}
rm -rf "$demo" && mkdir -p "$demo/frametool-py" && cd "$demo/frametool-py"
export UV_CACHE_DIR="$demo/cache"
tar -C "$src" --exclude=.venv --exclude=.hypothesis --exclude=.pytest_cache \
    --exclude=__pycache__ -cf - . | tar -xf -

echo "== 1. the copy as it is"
uv sync --quiet
uv run pytest -q -p no:cacheprovider | tail -1
uv run mypy --strict src tests

echo "== 2. the new dev line, then lock and sync"
cat > dev.txt <<'TOML'
dev = [
    "pytest>=8", "hypothesis>=6.100", "pyserial>=3.5", "types-pyserial>=3.5",
    "ruff>=0.6", "mypy>=1.11",
]
TOML
sed -i -e '/^dev = /{r dev.txt' -e 'd}' pyproject.toml
sed -n '/^\[dependency-groups\]/,/^$/p' pyproject.toml
uv lock 2>&1 | grep Added
uv sync --quiet --locked
uv pip list | grep -E '^(pyserial|types-pyserial) '

echo "== 3. tests and mypy --strict again"
uv run pytest -q -p no:cacheprovider | tail -1
uv run mypy --strict src tests
