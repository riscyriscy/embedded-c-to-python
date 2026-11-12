#!/usr/bin/env bash
# Run a single-file tool with inline metadata (PEP 723), then edit and lock its block.
# Run: bash uv_script_demo.sh   (needs uv, board_check.py beside it, access to PyPI)
set -u
here=$(cd "$(dirname "$0")" && pwd)
demo=${DEMO_DIR:-/tmp/uv_script_demo}
rm -rf "$demo" && mkdir -p "$demo/work" && cd "$demo/work"
export UV_CACHE_DIR="$demo/cache"    # an empty cache, so the first run has to fetch
cp "$here/board_check.py" .

echo "== 1. first run: uv builds an environment for the script"
uv run board_check.py
echo "== 2. second run: the cached environment is reused"
uv run board_check.py
echo "== 3. python3 ignores the block: pyserial is not installed for it"
python3 board_check.py 2>&1 | tail -1
echo "== 4. an environment that has pyserial runs it with plain python"
uv venv --quiet .venv && uv pip install --quiet pyserial
.venv/bin/python board_check.py | tail -1
echo "== 5. requires-python is checked against the interpreter that uv picks"
uv run --python 3.11 board_check.py 2>&1 | sed -n '1p;$p' | fold -s -w 88
uv run --python 3.12 board_check.py 2>&1 | tail -1
echo "== 6. uv add --script edits the comment block"
uv add --script board_check.py tabulate
head -7 board_check.py
echo "== 7. uv lock --script writes a lock file beside the script"
uv lock --script board_check.py
ls board_check.py*
grep -c '^\[\[package\]\]' board_check.py.lock
echo "== 8. uv export --script prints the pins as requirements.txt lines"
uv export --script board_check.py --no-hashes --no-annotate 2>&1 | grep -v Resolved
echo "== 9. uv remove --script takes the entry out again"
uv remove --script board_check.py tabulate
echo "== 10. a shebang line makes the script executable by itself"
(printf '#!/usr/bin/env -S uv run --script\n'; cat board_check.py) > check_direct.py
chmod +x check_direct.py && ./check_direct.py | tail -1
echo "== 11. in a project, a script with a block ignores the project's dependencies"
uv init --quiet --bare --name proj --python 3.12 proj && cd proj
uv add --quiet tabulate
printf 'import tabulate\nprint("tabulate imported")\n' > plain.py
printf '# /// script\n# dependencies = []\n# ///\nimport tabulate\n' > block.py
uv run plain.py
uv run block.py 2>&1 | tail -1
