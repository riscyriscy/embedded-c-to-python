#!/bin/sh
# Start the hanging tool with a SIGUSR1 handler, ask it for its stacks, then stop it.
# Run: sh hang_signal.sh
PY=${PY:-python3}
$PY hang_demo.py --signal &
PID=$!
sleep 1
kill -USR1 "$PID"
sleep 0.5
kill -0 "$PID" && echo "the process is still running"
kill "$PID"
