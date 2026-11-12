#!/usr/bin/env bash
# What --locked, --frozen and lock --check do when pyproject.toml and uv.lock disagree.
# Run: bash ci_lock_demo.sh   (needs uv, access to PyPI, and limitcheck/ beside it)
set -u
here=$(cd "$(dirname "$0")" && pwd)
demo=${DEMO_DIR:-/tmp/ci_lock_demo}
rm -rf "$demo" && mkdir -p "$demo" && cd "$demo"
export UV_CACHE_DIR="$demo/cache"
cp -r "$here/limitcheck" . && cd limitcheck
uv lock --quiet && uv sync --quiet --locked

echo "== 1. pyproject.toml gains a dependency by hand; uv.lock is not updated"
sed -i 's/^dependencies = \[\]/dependencies = ["tabulate>=0.10"]/' pyproject.toml
grep '^dependencies' pyproject.toml
echo "-- uv sync --locked"
uv sync --locked; echo "exit code $?"
echo "-- uv lock --check"
uv lock --check; echo "exit code $?"
echo "-- uv sync --frozen"
uv sync --frozen; echo "exit code $?"
echo "tabulate installed: $(uv pip list | grep -c tabulate)"

echo "== 2. uv lock repairs the lock; the locked sync then installs tabulate"
uv lock
uv sync --locked; echo "exit code $?"

echo "== 3. uv export includes the dev group and the project itself by default"
uv export --quiet --frozen --no-hashes -o requirements.txt
grep -E '^(-e|pytest==|tabulate==)' requirements.txt
echo "== 4. the same export, narrowed to what the tool needs at run time"
uv export --quiet --frozen --no-hashes --no-dev --no-emit-project \
    --no-annotate --no-header -o requirements.txt
cat requirements.txt
