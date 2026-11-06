#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Survey the two scripts that the flange real-motion script is built from:
  A) the station 仿真 script (continuous-motion logic source)
  B) the current 法兰真实运动 script (shell: 3 tabs + real-robot connection)
Print: top-level functions with line ranges, notebook tabs, and the key UI vars.
"""
import ast
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SIM = r"D:\mydata\working things\dobot_arm\RoboDK files 2\机械臂TCP仿真.py"
REAL = r"D:\mydata\workspace\机械臂法兰真实运动.py"

for tag, p in (("A 仿真(工作站/最新)", SIM), ("B 法兰真实运动(当前)", REAL)):
    src = io.open(p, encoding="utf-8").read()
    tree = ast.parse(src)
    lines = src.splitlines()
    print("=" * 78)
    print("%s   %s" % (tag, p))
    print("   %d lines, %d bytes" % (len(lines), len(src.encode("utf-8"))))
    print("-" * 78)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            args = [a.arg for a in node.args.args]
            print("   %4d-%-4d def %s(%s)" % (node.lineno, node.end_lineno, node.name, ", ".join(args)))
    print("-" * 78)
    for i, l in enumerate(lines, 1):
        s = l.strip()
        if ("notebook.add(" in s or "LabelFrame(" in s or "Button(" in s
                or "tk.Tk()" in s or "RUNMODE_" in s or "setRunMode" in s
                or "Connect()" in s or "StringVar(" in s):
            print("   %4d: %s" % (i, s[:110].encode("unicode_escape").decode("ascii")))
    print()
