"""`python -m pkgtool` runs this file after importing the package."""

import sys

print(f"pkgtool/__main__.py: running with __name__ = {__name__!r}")


def main() -> int:
    print(f"pkgtool called with arguments {sys.argv[1:]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
