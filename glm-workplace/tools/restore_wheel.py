#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# URGENT restore: wheel was left at in-base (179.665,-856,300) by the failed
# diag script. Undo the +100 base-Y push with its EXACT inverse transform.
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")
from robodk.robolink import *
from robodk.robomath import transl

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
w = RDK.Item('磨砂圆柱_R180_H40', ITEM_TYPE_OBJECT)
B = robot.Parent().PoseAbs()

cur = B.inv() * w.PoseAbs()
print("wheel in base NOW (pushed state):", ["%.3f" % v for v in cur.Pos()])

# exact inverse of: setPoseAbs(B * transl(0,+100,0) * B^-1 * old)
w.setPoseAbs(B * transl(0, -100, 0) * B.inv() * w.PoseAbs())

now = B.inv() * w.PoseAbs()
print("wheel in base AFTER restore      :", ["%.3f" % v for v in now.Pos()])
print("rotation rows (unchanged expected):")
for r in now.rows[:3]:
    print("   ", ["%8.4f" % v for v in r[:3]])
print("target was: (179.665, -956.000, 300.000)")
