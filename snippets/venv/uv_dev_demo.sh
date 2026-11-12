#!/usr/bin/env bash
# Development dependencies ([dependency-groups]) and the Python version pin with uv.
# Run: bash uv_dev_demo.sh   (needs uv and access to PyPI)
set -u
demo=${DEMO_DIR:-/tmp/uv_dev_demo}
rm -rf "$demo" && mkdir -p "$demo" && cd "$demo"
export UV_CACHE_DIR="$demo/cache"
uv init --quiet --bare --name rigtool --python 3.12 proj && cd proj
uv add --quiet pyserial
cp pyproject.toml before.toml

echo "== 1. uv add --dev writes a [dependency-groups] table; this is the change"
uv add --quiet --dev pytest ruff mypy
diff -u --label before --label after before.toml pyproject.toml

echo "== 2. uv sync --no-dev leaves only what the tool ships with"
uv sync --no-dev 2>&1 | grep -E '^(Uninstalled|Installed)'
uv pip list

echo "== 3. uv sync --group dev, or a plain uv sync, puts the tools back"
uv sync --group dev 2>&1 | grep -E '^(Uninstalled|Installed)'
uv sync --quiet --no-dev
uv sync 2>&1 | grep -E '^(Uninstalled|Installed)'
uv pip list | tail -n +3 | wc -l

echo "== 4. no pin: uv takes the newest interpreter that satisfies requires-python"
uv run python --version
echo "== 5. uv python pin writes .python-version and the environment follows it"
uv python pin 3.12
cat .python-version
uv run python --version 2>&1 | grep -v -E '^ ?(Downloading|Downloaded)'
echo "== 6. a pin outside requires-python is refused"
uv python pin 3.11 2>&1 | fold -s -w 88; echo "exit code ${PIPESTATUS[0]}"
echo "== 7. the interpreters uv can see"
uv python list --only-installed | awk '{print $1}' | uniq
