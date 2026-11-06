#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 精确 diff 待移植函数族，决定哪些必须整体替换
import io, sys, ast, difflib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace", line_buffering=True)

SIM = r"D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py"
REAL = r"D:\mydata\glm-workplace\sim_scripts\TCP真实运动_当前.py"

def load(path):
    src = io.open(path, encoding="utf-8", errors="replace").read()
    lines = src.splitlines()
    tree = ast.parse(src)
    out = {}
    for n in tree.body:
        if isinstance(n, ast.FunctionDef):
            out[n.name] = [l.rstrip() for l in lines[n.lineno - 1:n.end_lineno]]
    return out

fs, fr = load(SIM), load(REAL)

for name in ("_enable_obstacle_checks", "_check_single_joint_path", "_verify_obstacle_plan",
             "_trajectory_start_candidates", "_checked_j6_rewinds"):
    print("=" * 30, name, "=" * 30)
    d = list(difflib.unified_diff(fr[name], fs[name], "真实", "仿真", lineterm="", n=1))
    print("\n".join(d[:80]))
    print()
