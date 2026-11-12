# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.27"]
# ///
"""Single-file tool with its own dependencies (PEP 723). Run: uv run fetch_status.py"""

import httpx

print(f"httpx {httpx.__version__} available without a project or a manual venv")
