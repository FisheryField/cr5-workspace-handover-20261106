#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find the exact block boundaries needed to splice A's continuous-motion logic
into B (the flange real-motion script)."""
import ast
import io
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

A = r"D:\mydata\working things\dobot_arm\RoboDK files 2\机械臂TCP仿真.py"   # 仿真 (source of logic)
B = r"D:\mydata\workspace\机械臂法兰真实运动.py"                            # flange real-motion (shell)

for tag, p, ranges in (
        ("A", A, [(140, 250), (255, 275), (440, 470)]),
        ("B", B, [(270, 300), (380, 400), (470, 540), (650, 700), (780, 800), (955, 1160)]),
):
    lines = io.open(p, encoding="utf-8").read().splitlines()
    print("=" * 78)
    print("%s  %s  (%d lines)" % (tag, p, len(lines)))
    for lo, hi in ranges:
        print("-" * 78)
        print("   ... lines %d-%d" % (lo, hi))
        for i in range(lo - 1, min(hi, len(lines))):
            s = lines[i]
            if s.strip():
                st = s.strip()
                mark = "  <<<" if ("notebook.add" in st or st.startswith(("def ", "tab_", "frame_", "btn_", "root.mainloop")) or "StringVar" in st) else ""
                print("   %4d: %s%s" % (i + 1, st[:112].encode("unicode_escape").decode("ascii"), mark))
    print()
