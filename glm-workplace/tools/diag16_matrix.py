#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Diag16 (matrix completion, read-only): fill the last cells of the
# pair-alive/dead matrix at the parked pose.
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")
from robodk.robolink import *
from robodk.robomath import transl

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
w = RDK.Item('磨砂圆柱_R180_H40', ITEM_TYPE_OBJECT)
tool = RDK.Item('门把手_bs1', ITEM_TYPE_TOOL)
table = RDK.Item('安装台_650x650x80mm', ITEM_TYPE_OBJECT)
floor = RDK.Item('地面_禁止穿越', ITEM_TYPE_OBJECT)
B = robot.Parent().PoseAbs()

# engulf the wrist with the TABLE temporarily (table onto flange region)
saved_t = table.PoseAbs()
fl_world = (B * robot.Pose()).Pos()
table.setPoseAbs(transl(fl_world[0]-saved_t.Pos()[0], fl_world[1]-saved_t.Pos()[1],
                        fl_world[2]-saved_t.Pos()[2]) * saved_t)
print("table engulfing FLANGE:")
print("  Collision(robot, table) = %d  (1 expected if robot-side pairs work)" % RDK.Collision(robot, table))
print("  Collision(tool, table)  = %d" % RDK.Collision(tool, table))
table.setPoseAbs(saved_t)

print("\nat-rest pairs (sanity):")
print("  Collision(tool, floor) = %d (0 expected)" % RDK.Collision(tool, floor))
print("  Collision(robot, table) at rest = %d (0 expected)" % RDK.Collision(robot, table))
print("  Collision(tool, wheel) at rest (delta=5mm) = %d  <- THE goal pair" % RDK.Collision(tool, w))
