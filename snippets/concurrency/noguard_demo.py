"""A ProcessPoolExecutor job with no main guard. Run: python3 noguard_demo.py"""

import concurrent.futures as cf


def square(n: int) -> int:
    return n * n


with cf.ProcessPoolExecutor(max_workers=2) as pool:
    print(list(pool.map(square, range(5))))
