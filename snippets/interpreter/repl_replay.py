"""Replay a list of lines through the interactive console, echoing the prompts as the REPL shows them."""
import code
import sys

console = code.InteractiveConsole()
more = False
for line in open(sys.argv[1]).read().split("\n")[:-1]:
    print(("... " if more else ">>> ") + line)
    more = console.push(line)
