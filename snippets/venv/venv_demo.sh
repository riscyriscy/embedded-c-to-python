#!/usr/bin/env bash
# Virtual environments with venv and pip, and a reproducible requirements.txt.
# Run: PYTHON=python3.14 bash venv_demo.sh      (needs network access to PyPI)
set -eu
PYTHON=${PYTHON:-python3}
here=$(cd "$(dirname "$0")" && pwd)
demo=${DEMO_DIR:-/tmp/venv_demo}
rm -rf "$demo" && mkdir -p "$demo/rig" && cd "$demo/rig"

echo "== 1. create the environment"
$PYTHON --version
$PYTHON -m venv .venv
ls -a
cat .venv/pyvenv.cfg
# ASCII names only: Python 3.14 also adds an alias spelled with the Greek letter pi
ls .venv/bin | grep '^[ -~]*$'

echo "== 2. activation only changes PATH and the prompt"
echo "before: $(command -v python)"
. .venv/bin/activate
echo "after:  $(command -v python)"
echo "VIRTUAL_ENV=$VIRTUAL_ENV"

echo "== 3. install the direct dependencies from requirements.in"
cat > requirements.in <<'REQ'
# Direct dependencies, with compatible version ranges
pyserial>=3.5,<4
python-can>=4.6,<5
REQ
python -m pip install --quiet --disable-pip-version-check -r requirements.in
python -m pip list --disable-pip-version-check

echo "== 4. freeze the exact versions into requirements.txt"
python -m pip freeze > requirements.txt
cat requirements.txt
deactivate
echo "after deactivate: $(command -v python)"

echo "== 5. rebuild from requirements.txt in a fresh environment"
$PYTHON -m venv .venv-copy
.venv-copy/bin/python -m pip install --quiet --disable-pip-version-check -r requirements.txt
.venv-copy/bin/python -m pip freeze > copy.txt
diff requirements.txt copy.txt && echo "the two environments are identical"
.venv-copy/bin/python -m pip check --disable-pip-version-check

echo "== 6. run a script with and without the environment (no activation needed)"
$PYTHON "$here/venv_info.py"
.venv/bin/python "$here/venv_info.py"
