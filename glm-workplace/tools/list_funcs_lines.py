#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 列出仿真副本中待移植函数的行号范围 + 关键片段
import io, sys, ast
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace", line_buffering=True)

SIM = r"D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py"
REAL = r"D:\mydata\glm-workplace\sim_scripts\TCP真实运动_当前.py"

for tag, path in (("仿真", SIM), ("真实", REAL)):
    src = io.open(path, encoding="utf-8", errors="replace").read()
    tree = ast.parse(src)
    print("== %s 函数行号 ==" % tag)
    for n in tree.body:
        if isinstance(n, ast.FunctionDef):
            print("  %-46s L%d-%d (%d行)" % (n.name, n.lineno, n.end_lineno, n.end_lineno - n.lineno + 1))
    print()

# 真实脚本里 _validated_records 对 spin360/j6_delta 的限制、GUI deviation 默认值
src = io.open(REAL, encoding="utf-8", errors="replace").read().splitlines()
for i, l in enumerate(src, 1):
    if "j6_delta" in l or "spin" in l.lower() or "real_deviation" in l or "180" in l and "delta" in l.lower():
        print("真实 L%d: %s" % (i, l.rstrip()))
