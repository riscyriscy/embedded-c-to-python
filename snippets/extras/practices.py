"""Standard-library habits for host tools. Run: python3 practices.py"""

from __future__ import annotations

import hashlib
import itertools
import logging
import os
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# logging, not print: levels, timestamps, module names, and one switch to make it verbose
log = logging.getLogger("practices")  # one logger per module, named after it


def sha256_file(path: Path, chunk: int = 1 << 16) -> str:
    """Hash a firmware image without loading it all into memory."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    """Readers see the old file or the new one, never a half-written one."""
    tmp = path.with_name(
        f".{path.name}.{secrets.token_hex(4)}.tmp"
    )  # same directory, same file system
    fd = os.open(
        tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666
    )  # the umask trims it, as for open()
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())  # the data is on disk before the rename
        if path.exists():
            os.chmod(tmp, stat.S_IMODE(path.stat().st_mode))  # keep the mode of the old file
        tmp.replace(path)  # atomic rename on the same file system
    except BaseException:
        tmp.unlink(missing_ok=True)  # do not leave a temporary file behind
        raise
    if hasattr(os, "O_DIRECTORY"):  # POSIX: make the rename itself survive a power failure
        dir_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)


def run_tool(*cmd: str, timeout: float = 10.0) -> str:
    """Run an external tool safely: argument list (no shell), timeout, error on failure."""
    log.debug("running %s", cmd)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=True)
    return result.stdout.strip()


def main() -> None:
    logging.basicConfig(
        level=logging.DEBUG if "-v" in sys.argv else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    work = Path(tempfile.mkdtemp(prefix="fw-"))
    image = work / "fw.bin"
    atomic_write(image, bytes(range(256)) * 4096)  # 1 MiB
    log.info(
        "wrote %s (%d bytes), sha256 %s...",
        image.name,
        image.stat().st_size,
        sha256_file(image)[:16],
    )

    plain = work / "plain.bin"
    plain.write_bytes(b"")  # a file made by open() is the reference for the mode
    same_mode = stat.S_IMODE(image.stat().st_mode) == stat.S_IMODE(plain.stat().st_mode)
    log.info("mode of the written file matches a file made by open(): %s", same_mode)
    (work / "blocked").mkdir()  # a directory cannot be replaced by a file
    try:
        atomic_write(work / "blocked", b"x")
    except OSError as e:
        left = len(list(work.glob(".*.tmp")))
        log.info("replace failed with %s; temporary files left: %d", type(e).__name__, left)

    # time.monotonic for intervals: never jumps when NTP adjusts the wall clock
    t0 = time.monotonic()
    out = run_tool(sys.executable, "-c", "import platform; print(platform.python_version())")
    log.info("child interpreter reports Python %s in %.0f ms", out, (time.monotonic() - t0) * 1e3)

    try:
        run_tool(sys.executable, "-c", "raise SystemExit(3)")
    except subprocess.CalledProcessError as e:
        log.warning("tool failed with exit code %d", e.returncode)

    log.info("objcopy on PATH: %s", shutil.which("arm-none-eabi-objcopy") or "not found")

    # itertools.batched (3.12+): fixed-size chunks, e.g. for a bootloader's write-block size
    blocks = list(itertools.batched(range(10), 4))
    log.info("batched(range(10), 4) -> %s", blocks)

    shutil.rmtree(work)  # clean up the temporary directory
    log.debug("removed %s", work)


if __name__ == "__main__":  # import without side effects; run as a script
    main()
