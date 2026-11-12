#!/usr/bin/env bash
# The same workflow with uv: a venv, requirements.txt from requirements.in, and uv.lock.
# Run: bash uv_demo.sh      (needs uv and network access to PyPI)
set -eu
demo=${DEMO_DIR:-/tmp/uv_demo}
rm -rf "$demo" && mkdir -p "$demo/rig" && cd "$demo/rig"

echo "== 1. a venv and requirements.txt, pip style"
uv venv --quiet --python 3.14
cat > requirements.in <<'REQ'
pyserial>=3.5,<4
python-can>=4.6,<5
REQ
uv pip compile --quiet requirements.in -o requirements.txt
cat requirements.txt
uv pip sync --quiet requirements.txt
uv pip list

echo "== 2. the same pins with hashes, installed with hash checking"
uv pip compile --quiet --generate-hashes requirements.in -o hashed.txt
head -8 hashed.txt
uv venv --quiet .venv-hashed
uv pip install --quiet --python .venv-hashed --require-hashes -r hashed.txt
echo "installed with --require-hashes"

echo "== 3. a project: pyproject.toml and uv.lock replace both files"
cd "$demo" && uv init --quiet --bare --name rig proj && cd proj
uv add --quiet --python 3.14 "pyserial>=3.5,<4" "python-can>=4.6,<5"
cat pyproject.toml
ls -a
grep -c '^\[\[package\]\]' uv.lock
uv run --quiet python -c "import serial; print('pyserial', serial.__version__)"

echo "== 4. export a requirements.txt for tools that want one"
uv export --quiet --no-hashes --no-emit-project --no-annotate -o requirements.txt
cat requirements.txt
