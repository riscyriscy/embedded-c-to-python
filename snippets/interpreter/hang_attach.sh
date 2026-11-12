#!/bin/sh
# Start the tool in polling mode and attach pdb to it (Python 3.14, same user for both processes).
# Run: sh hang_attach.sh
PY=${PY:-python3}
$PY hang_demo.py --poll >/dev/null &
PID=$!
sleep 1
$PY pty_drive.py "(Pdb) " "where;up;l;c" $PY -m pdb -p "$PID"
kill "$PID"
