#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Diag9 (final isolation): is the TOOL blind to everything, or just to the wheel?
#  A) temp-move TABLE onto the tool rod (dense, unambiguous chunk) -> Collision(tool, table)
#  B) temp-move WHEEL onto the tool rod                               -> Collision(tool, wheel)
#  C) exact-restore both, re-verify
# Rod (base frame): x in [175.7,183.6], y in [-781.0,-768.6], z in [287.7,312.3]
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
print("parked joints (untouched):", ["%.1f" % v for v in q])

rod_center_base = (179.6, -774.8, 300.0)
rod_center_world = (B * transl(*rod_center_base)).Pos()

# --- A) table onto the rod ---
t_saved = table.PoseAbs()
t_delta = (rod_center_world[0]-t_saved.Pos()[0], rod_center_world[1]-t_saved.Pos()[1],
           rod_center_world[2]-t_saved.Pos()[2])
table.setPoseAbs(transl(*t_delta) * t_saved)
ca = RDK.Collision(tool, table)
print("A) Collision(tool, table) with table engulfing the rod = %d   (1 expected)" % ca)
table.setPoseAbs(t_saved)

# --- B) wheel onto the rod ---
w_saved = w.PoseAbs()
w_delta = (rod_center_world[0]-w_saved.Pos()[0], rod_center_world[1]-w_saved.Pos()[1],
           rod_center_world[2]-w_saved.Pos()[2])
w.setPoseAbs(transl(*w_delta) * w_saved)
cb = RDK.Collision(tool, w)
print("B) Collision(tool, wheel) with wheel engulfing the rod = %d  (1 expected)" % cb)
# extra: full map on during engulf
RDK.setCollisionActive(COLLISION_ON)
cb2 = RDK.Collisions()
print("B2) global map ON, Collisions() during wheel-rod engulf = %d   (>0 expected)" % cb2)
w.setPoseAbs(w_saved)

# --- C) verify restores ---
print("\nC) restored: table world", ["%.2f" % v for v in table.PoseAbs().Pos()])
inb = B.inv() * w.PoseAbs()
print("   wheel in-base (%.2f, %.2f, %.2f)" % tuple(v for v in inb.Pos()[:3]))
print("   Collision(tool, table) at rest = %d (0 expected)" % RDK.Collision(tool, table))
print("   Collision(w, table)   at rest = %d (0 expected)" % RDK.Collision(w, table))
