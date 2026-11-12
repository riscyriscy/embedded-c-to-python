"""Threads, queues and the asyncio bridge. Run: python3 threads_demo.py"""

import asyncio
import queue
import signal
import sys
import threading
import time


def blocking_read() -> bytes:  # stands in for a pyserial read
    time.sleep(0.01)
    return b"\xa5\x01"


def count(use_lock: bool) -> int:
    lock, box = threading.Lock(), [0]

    def work() -> None:
        for _ in range(200_000):
            if use_lock:
                with lock:
                    box[0] += 1
            else:
                box[0] += 1  # load, add, store: three steps, not one

    threads = [threading.Thread(target=work) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return box[0]


def producer(q: "queue.Queue[int | None]") -> None:  # stands in for a UART RX thread
    for byte in range(8):
        q.put(byte)  # blocks while the queue is full: backpressure
    q.put(None)  # sentinel: no more data


def queues() -> None:
    q: queue.Queue[int | None] = queue.Queue(maxsize=3)
    try:
        q.get(timeout=0.02)
    except queue.Empty:
        print("  get(timeout) on an empty queue raised queue.Empty")
    for n in range(3):
        q.put_nowait(n)
    try:
        q.put(9, timeout=0.02)
    except queue.Full:
        print("  put(timeout) on a full queue raised queue.Full")
    q = queue.Queue(maxsize=3)  # a fresh, empty queue for the producer
    prod = threading.Thread(target=producer, args=(q,))
    prod.start()
    time.sleep(0.05)  # the consumer starts late: the producer fills the queue
    print(f"  producer blocked with the queue at {q.qsize()} of {q.maxsize}")
    received: list[int] = []
    while (item := q.get(timeout=1)) is not None:
        received.append(item)
    prod.join()
    print(f"  consumer received {received} then the sentinel")
    if sys.version_info >= (3, 13):
        q.shutdown()
        try:
            q.get()
        except queue.ShutDown:
            print("  3.13+: get() after shutdown() raised queue.ShutDown")
    else:
        print("  3.12: Queue.shutdown() does not exist, use the sentinel")


def bridge() -> None:
    async def main() -> None:
        loop = asyncio.get_running_loop()
        aq: asyncio.Queue[int] = asyncio.Queue()

        async def answer() -> str:
            return f"ran in {threading.current_thread().name}"

        def uart_rx() -> None:  # runs in a plain thread
            for byte in (0xA5, 0x01, 0x02):
                loop.call_soon_threadsafe(aq.put_nowait, byte)  # never aq.put_nowait
            reply = asyncio.run_coroutine_threadsafe(answer(), loop)
            print(f"  run_coroutine_threadsafe: {reply.result(timeout=1)}")
            try:
                loop.call_soon(print, "never")  # wrong thread: checked in debug mode
            except RuntimeError:
                print("  loop.call_soon from a thread raised RuntimeError (debug mode)")

        rx = asyncio.create_task(asyncio.to_thread(uart_rx))
        got = [await aq.get() for _ in range(3)]
        await rx
        print(f"  asyncio side received {[hex(b) for b in got]}")
        print(f"  to_thread(blocking_read): {await asyncio.to_thread(blocking_read)!r}")
        fut = loop.create_future()
        loop.call_later(0.01, fut.set_result, "call_later fired")
        print(f"  {await fut}")

    asyncio.run(main(), debug=True)


def primitives() -> None:
    lock, rlock = threading.Lock(), threading.RLock()
    lock.acquire()
    rlock.acquire()
    errors: list[str] = []

    def release_elsewhere() -> None:
        lock.release()  # allowed: a Lock has no owner
        try:
            rlock.release()
        except RuntimeError as exc:
            errors.append(str(exc))

    other = threading.Thread(target=release_elsewhere)
    other.start()
    other.join()
    print(f"  Lock released by another thread, locked() is now {lock.locked()}")
    print(f"  RLock released by another thread raised RuntimeError: {errors[0]}")
    bits, cond = [0], threading.Condition()

    def wait_for_both() -> None:
        with cond:
            ok = cond.wait_for(lambda: bits[0] & 0b101 == 0b101, timeout=1)
        print(f"  Condition.wait_for returned {ok}, bits={bits[0]:#05b}")

    waiter = threading.Thread(target=wait_for_both)
    waiter.start()
    for flag in (0b001, 0b100):
        with cond:
            bits[0] |= flag
            cond.notify_all()
    waiter.join()
    fired = threading.Event()
    threading.Timer(0.01, fired.set).start()
    print(f"  threading.Timer fired: {fired.wait(1)}")


def shutdown() -> None:
    stop = threading.Event()
    workers = [threading.Thread(target=stop.wait) for _ in range(2)]
    workers.append(threading.Thread(target=time.sleep, args=(60,), daemon=True))
    for w in workers:
        w.start()
    try:
        signal.raise_signal(signal.SIGINT)  # what Ctrl+C does
        time.sleep(1)
    except KeyboardInterrupt:
        print(f"  KeyboardInterrupt arrived in {threading.current_thread().name}")
        stop.set()
    for w in workers[:2]:
        w.join()
    print(f"  workers stopped: {[not w.is_alive() for w in workers[:2]]}")
    print(f"  daemon thread still running: {workers[2].is_alive()}")


def main() -> None:
    print("1. counter += 1 from four threads, 800000 expected")
    print(f"  with a lock:    {count(True)}")
    print(f"  without a lock: {count(False)}  (varies)")
    print("2. queue.Queue(maxsize=3)")
    queues()
    print("3. thread to asyncio")
    bridge()
    print("4. lock, RLock, Condition, Timer")
    primitives()
    print("5. shutdown")
    shutdown()


if __name__ == "__main__":
    main()
