"""A misspelt marker. Run: pytest -q demo_typo.py"""

import pytest


@pytest.mark.hardwre
def test_x() -> None: ...
