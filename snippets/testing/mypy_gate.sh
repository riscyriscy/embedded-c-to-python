#!/usr/bin/env bash
# The mypy --strict gate: stubs for pyserial, and which other stub packages exist.
# Run: bash mypy_gate.sh   (needs uv, access to PyPI, and port_scan.py beside it)
set -u
here=$(cd "$(dirname "$0")" && pwd)
demo=${DEMO_DIR:-/tmp/mypy_gate}
rm -rf "$demo" && mkdir -p "$demo/scan" && cd "$demo/scan"
export UV_CACHE_DIR="$demo/cache"
cp "$here/port_scan.py" . && uv init --quiet --bare --name scan --python 3.12 .
uv add --quiet pyserial && uv add --quiet --dev mypy

echo "== 1. pyserial installed, no stubs"
uv run mypy --strict port_scan.py | fold -s -w 88; echo "exit code ${PIPESTATUS[0]}"

echo "== 2. types-pyserial added to the dev group"
uv add --dev types-pyserial 2>&1 | grep -E '^ \+'
sed -n '/^\[dependency-groups\]/,$p' pyproject.toml
uv run mypy --strict port_scan.py; echo "exit code $?"

echo "== 3. which stub packages exist (uv pip install --dry-run)"
uv venv --quiet probe
for p in types-pyserial types-psutil types-reportlab types-pyusb types-plotly; do
    if out=$(uv pip install --python probe --dry-run "$p" 2>&1); then
        echo "$p: $(echo "$out" | grep -m1 -E '^ \+' | sed 's/^ *+ //')"
    else
        echo "$p: $(echo "$out" | grep -m1 -o 'was not found in the package registry')"
    fi
done

echo "== 4. do the libraries themselves ship py.typed or .pyi files?"
uv pip install --quiet --python probe pyserial psutil reportlab pyusb plotly
for m in serial psutil reportlab usb plotly; do
    d=$(probe/bin/python -c "import $m, os; print(os.path.dirname($m.__file__))")
    n=$(find "$d" \( -name py.typed -o -name '*.pyi' \) | wc -l)
    echo "$m: $n files"
done
