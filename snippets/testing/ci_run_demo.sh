#!/usr/bin/env bash
# Run limitcheck/ci.sh on a fresh copy, then break the formatting and run it again.
# Run: bash ci_run_demo.sh   (needs uv, access to PyPI, and limitcheck/ beside it)
set -u
here=$(cd "$(dirname "$0")" && pwd)
demo=${DEMO_DIR:-/tmp/ci_run_demo}
rm -rf "$demo" && mkdir -p "$demo" && cd "$demo"
export UV_CACHE_DIR="$demo/cache"
cp -r "$here/limitcheck" . && cd limitcheck
uv lock --quiet && uv sync --quiet --locked   # a runner whose cache is warm

echo "== 1. a clean tree: every step passes"
bash ci.sh; echo "ci.sh exit code $?"

echo "== 2. what the runner leaves behind"
ls -a | grep -E 'cache|report' | sort
grep -o '<testsuite [^>]*>' report.xml | sed 's/ hostname="[^"]*"//' \
    | sed 's/ \([a-z]*=\)/\n    \1/g'

echo "== 3. one single-quoted string: the script stops at the format check"
sed -i "s/return \"NAN\"/return 'NAN'/" src/limitcheck/limits.py
bash ci.sh; echo "ci.sh exit code $?"
