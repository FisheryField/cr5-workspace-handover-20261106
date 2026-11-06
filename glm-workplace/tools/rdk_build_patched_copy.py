#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Build patched copy of the authoritative TCP sim script.
# Exactly two changes; every change must match exactly once or we abort.
import sys, io, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SRC = r"D:\mydata\working things\dobot_arm\RoboDK files 2\机械臂TCP仿真.py"
DST = r"D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py"

with open(SRC, "r", encoding="utf-8") as f:
    src = f.read()

PATCHES = [
    # 1) wheel into obstacle whitelist
    ("for name in ('安装台_650x650x80mm', '地面_禁止穿越'):",
     "for name in ('安装台_650x650x80mm', '地面_禁止穿越', '磨砂圆柱_R180_H40'):"),
    # 2) whole-plan verify guard: some RoboDK builds return positive status
    #    with 'Collisions found.' message instead of negative status.
    ("""        message, matrix, status = program.InstructionListJoints(
            mm_step=1, deg_step=1, collision_check=COLLISION_ON)
        if status < 0:
            raise ValueError('整段碰撞复核未通过：' + message)""",
     """        message, matrix, status = program.InstructionListJoints(
            mm_step=1, deg_step=1, collision_check=COLLISION_ON)
        if status < 0 or 'collision' in message.lower():
            raise ValueError('整段碰撞复核未通过：' + message)"""),
]

out = src
for i, (old, new) in enumerate(PATCHES, 1):
    n = out.count(old)
    if n != 1:
        print("ABORT: patch %d matched %d times (expect 1)" % (i, n)); sys.exit(1)
    out = out.replace(old, new)
    print("patch %d applied (delta %+d chars)" % (i, len(new) - len(old)))

with open(DST, "w", encoding="utf-8", newline="") as f:
    f.write(out)

import py_compile
py_compile.compile(DST, doraise=True)
print("py_compile OK ->", DST)
h = lambda p: hashlib.md5(open(p, "rb").read()).hexdigest()
print("md5 src:", h(SRC))
print("md5 dst:", h(DST))
print("size src/dst:", len(src.encode('utf-8')), len(out.encode('utf-8')))
