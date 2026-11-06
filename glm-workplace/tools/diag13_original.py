#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Diag13: ORIGINAL station wheel engulfing the TABLE (native x native,
# non-robot pair) - already shown =1 in diag6. Re-confirm + also engulf the
# FLANGE region with the original wheel while checking robot-link pairs one
# by one via Collision(robot, w) with global map ON.
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")
from robodk.robolink import *
from robodk.robomath import transl

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
w = RDK.Item('磨砂圆柱_R180_H40', ITEM_TYPE_OBJECT)
table = RDK.Item('安装台_650x650x80mm', ITEM_TYPE_OBJECT)
tool = RDK.Item('门把手_bs1', ITEM_TYPE_TOOL)
B = robot.Parent().PoseAbs()

saved = w.PoseAbs()

# A) original wheel onto table (control re-confirm)
t = table.PoseAbs()
d = (t.Pos()[0]-saved.Pos()[0], t.Pos()[1]-saved.Pos()[1], 40.0-saved.Pos()[2])
w.setPoseAbs(transl(*d) * saved)
print("A) original wheel engulfing table: Collision = %d  (1 expected)" % RDK.Collision(w, table))
w.setPoseAbs(saved)

# B) original wheel engulfing the FOREARM region (in-base y -600, mid-arm)
w.setPoseAbs(B * transl(100, -600, 300) * B.inv() * saved)
RDK.setCollisionActive(COLLISION_ON)
print("B) wheel at forearm region (100,-600,300): Collision(robot,w) = %d" % RDK.Collision(robot, w))
for it, tag in [(tool, 'tool'), (table, 'table')]:
    print("   Collision(%s, w) = %d" % (tag, RDK.Collision(it, w)))

w.setPoseAbs(saved)
print("\nrestored wheel in-base: (%.2f, %.2f, %.2f)"
      % tuple(v for v in (B.inv()*w.PoseAbs()).Pos()[:3]))
