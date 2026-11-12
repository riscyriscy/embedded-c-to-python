"""Send Tcl commands to OpenOCD over its RPC port, using the dummy adapter.

Run: python3 openocd_tcl.py
"""

import logging
import socket
import subprocess
import time
from typing import Self

log = logging.getLogger("openocd")
TERMINATOR = b"\x1a"  # ends each command and each reply
OPENOCD = [
    "openocd",
    "-c", "adapter driver dummy",
    "-c", "adapter speed 1000",
    "-c", "gdb_port disabled",
    "-c", "telnet_port disabled",
    "-c", "tcl_port 6666",
]  # fmt: skip


class OpenOcdTcl:
    def __init__(self, host: str = "127.0.0.1", port: int = 6666) -> None:
        self._sock = socket.create_connection((host, port), timeout=5.0)

    def command(self, tcl: str) -> str:
        log.debug("send %r", tcl)
        self._sock.sendall(tcl.encode() + TERMINATOR)
        reply = bytearray()
        while not reply.endswith(TERMINATOR):
            chunk = self._sock.recv(4096)
            if not chunk:
                raise ConnectionError("OpenOCD closed the connection")
            reply += chunk
        return reply[:-1].decode()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        self._sock.close()


def connect(deadline_s: float = 5.0) -> OpenOcdTcl:
    """OpenOCD needs a moment to open its port: retry until the deadline."""
    end = time.monotonic() + deadline_s
    while True:
        try:
            return OpenOcdTcl()
        except ConnectionRefusedError:
            if time.monotonic() > end:
                raise
            time.sleep(0.05)


def main() -> None:
    server = subprocess.Popen(
        OPENOCD, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    try:
        with connect() as ocd:
            for tcl in ("version", "expr {6 * 7}", "adapter speed", "no_such_command"):
                print(f"{tcl!r} -> {ocd.command(tcl)!r}")
            print(f"'shutdown' -> {ocd.command('shutdown')!r}")
        print("openocd exit code:", server.wait(timeout=5))
    finally:
        if server.poll() is None:  # something failed before shutdown
            server.kill()


if __name__ == "__main__":
    main()
