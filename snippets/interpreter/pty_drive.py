"""Run a command under a pseudo-terminal, send one line after each prompt, and print the transcript."""
import os
import pty
import re
import select
import sys

prompt = sys.argv[1].encode()
commands = [c.encode() + b"\n" for c in sys.argv[2].split(";")]
cmd = sys.argv[3:]
pid, fd = pty.fork()
if pid == 0:
    os.execvp(cmd[0], cmd)
out = b""
queue = list(commands)
while True:
    r, _, _ = select.select([fd], [], [], 5)
    if not r:
        break
    try:
        chunk = os.read(fd, 4096)
    except OSError:
        break
    if not chunk:
        break
    out += chunk
    if out.endswith(prompt) and queue:
        os.write(fd, queue.pop(0))
text = out.decode(errors="replace").replace("\r\n", "\n").replace("\r", "")
text = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text)
print(text, end="")
