#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 完整导出 TCP真实运动 代码（<br> -> \n），并查站目录下的 .py 宏文件
import sys, io, os, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace", line_buffering=True)
from robodk.robolink import Robolink

RDK = Robolink()
prog = RDK.Item("TCP真实运动")
code = prog.setParam("Code")
if "<br>" in code:
    code = code.replace("<br>", "\n")

dst = r"D:\mydata\glm-workplace\sim_scripts\TCP真实运动_当前.py"
with open(dst, "w", encoding="utf-8") as f:
    f.write(code)
print("导出:", dst, len(code), "字符")

import ast
try:
    tree = ast.parse(code)
    print("语法 OK")
    for n in tree.body:
        if isinstance(n, ast.FunctionDef):
            print("def %-46s L%d-%d" % (n.name, n.lineno, n.end_lineno))
except SyntaxError as e:
    print("!! 语法错误:", e)

print("\n== 站目录下的 py 文件 ==")
base = r"D:\mydata\working things\dobot_arm\RoboDK files 2"
for p in sorted(glob.glob(base + r"\*.py")) + sorted(glob.glob(base + r"\*.rdk")):
    print("  %-52s %8d B  %s" % (os.path.basename(p), os.path.getsize(p), os.path.getmtime()))
