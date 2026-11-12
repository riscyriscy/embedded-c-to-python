"""Import rigtool and call one of its functions. main() does not run."""

import rigtool

print(f"use_rigtool: __name__ = {__name__!r}")
mean = rigtool.average_mv([3300, 3302])
print(f"use_rigtool: average_mv([3300, 3302]) = {mean}")
