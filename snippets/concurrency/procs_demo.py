"""Process pools: start methods, the main guard, pickling. Run: python3 procs_demo.py"""

import concurrent.futures as cf
import multiprocessing as mp
import pickle
import sys

GAIN = {"value": 1}  # module state: a forked child sees changes, a spawned one does not


def square(n: int) -> int:
    return n * n


def read_gain() -> int:
    return GAIN["value"]


def main() -> None:
    print(f"start method: {mp.get_start_method()}")
    GAIN["value"] = 2  # set after import, before the first task is submitted
    with cf.ProcessPoolExecutor(max_workers=2) as pool:
        print(f"pool.map(square, range(5)) -> {list(pool.map(square, range(5)))}")
        print(f"child reads GAIN = {pool.submit(read_gain).result()}")
        try:
            pool.submit(lambda: 1).result()
        except (pickle.PicklingError, AttributeError) as exc:
            print(f"a lambda cannot be sent: {type(exc).__name__}")
    if sys.version_info >= (3, 14):
        with cf.InterpreterPoolExecutor(max_workers=2) as ipool:
            print(f"InterpreterPoolExecutor -> {list(ipool.map(square, range(5)))}")
    else:
        print("InterpreterPoolExecutor: not in 3.12")


if __name__ == "__main__":  # a spawned child imports this file and must not run main()
    main()
