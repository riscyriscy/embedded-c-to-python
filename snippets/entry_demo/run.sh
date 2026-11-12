#!/usr/bin/env bash
# Run the entry-point examples and show the output and exit status of each.
# Run: bash run.sh   (PYTHON=python3.12 bash run.sh picks an interpreter)
cd "$(dirname "$0")" || exit 1
py() {
    echo "\$ python $*"
    "${PYTHON:-python3}" "$@"
    echo "exit status $?"
    echo
}
py rigtool.py 3
py -m rigtool 3
py rigtool.py
py use_rigtool.py
py -m pkgtool 3
