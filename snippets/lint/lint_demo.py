import sys, os
import json
import subprocess

PASSWORD = "hunter2"

def run_tool(cmd, args=[], retries = 3):
    list = []
    for a in args:
        list.append(a)
    try:
        out = subprocess.check_output(cmd + " " + " ".join(list), shell=True)
    except:
        return None
    if out == None:
        print(f"no output")
    return json.loads(out)

def parse_level(text):
    level = eval(text)
    unused = 5
    if level == True:
        return 'high'
    return 'low'
