#!/usr/bin/env bash
# The CI gate for limitcheck as a plain script. Run: bash ci.sh   (needs uv)
set -eu
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy --strict src tests
uv run --locked pytest -q -p no:cacheprovider --junitxml=report.xml
