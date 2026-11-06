#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Diag4 (decisive, pair-direct): use RDK.Collision(item1,item2) which works
# independently of the collision map.
#  P) positive control: temp-push wheel +100 base-Y (deep into tool), expect 1
#  N) negative control: tool vs table (parked pose), expect 0
#  T) the real question: tool vs wheel at current (179.665,-956,300) = 5mm
#     short-end penetration, expect 1 (contact achieved)
# Exact-restore the wheel after the push. No joint moves.
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")
from robodk.robolink import *
from robodk.robomath import transl

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
w = RDK.Item('磨砂圆柱_R180_H40', ITEM_TYPE_OBJECT)
tool = RDK.Item('门把手_bs1', ITEM_TYPE_TOOL)
table = RDK.Item('安装台_650x650x80mm', ITEM_TYPE_OBJECT)
B = robot.Parent().PoseAbs()
q = robot.Joints().list()[:6]
print("parked joints:", ["%.3f" % v for v in q])

saved_world = w.PoseAbs()   # good state (179.665,-956,300)

# T) real question first, at current pose
inb = B.inv() * saved_world
print("\n[T] wheel in-base: (%.2f, %.2f, %.2f)" % tuple(v for v in inb.Pos()[:3]))
print("[T] RDK.Collision(tool, wheel) at 5mm depth =", RDK.Collision(tool, w), "(1 = contact)")

# N) negative control
print("[N] RDK.Collision(tool, table) =", RDK.Collision(tool, table), "(0 expected)")

# P) positive control: deep push, exact restore
w.setPoseAbs(B * transl(0, 100, 0) * B.inv() * saved_world)
print("[P] RDK.Collision(tool, wheel) with +100Y push =", RDK.Collision(tool, w), "(1 expected)")

# restore exactly
w.setPoseAbs(saved_world)
inb2 = B.inv() * w.PoseAbs()
print("\nrestored wheel in-base: (%.2f, %.2f, %.2f)" % tuple(v for v in inb2.Pos()[:3]))
print("[T2] RDK.Collision(tool, wheel) after restore =", RDK.Collision(tool, w))
