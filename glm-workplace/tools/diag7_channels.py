#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Diag7 (final isolation): with wheel deep-pushed into the tool (+100 base-Y,
# massive overlap), compare detection channels:
#   1. tool item pose (is tool geometry really on the flange?)
#   2. RDK.Collision(w, tool)          -- direct pair (blind so far)
#   3. RDK.Collision(robot, w)         -- direct pair vs robot (any link)
#   4. MoveJ_Test with ONLY (tool,w) ON
#   5. MoveJ_Test with ONLY (robot,w) ON
# Then exact-restore wheel. No joint motion.
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")
from robodk.robolink import *
from robodk.robomath import transl

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
w = RDK.Item('磨砂圆柱_R180_H40', ITEM_TYPE_OBJECT)
tool = RDK.Item('门把手_bs1', ITEM_TYPE_TOOL)
B = robot.Parent().PoseAbs()
q = robot.Joints().list()[:6]

print("1) tool PoseAbs pos:", ["%.1f" % v for v in tool.PoseAbs().Pos()],
      " (flange world ~ 818,635,397 expected)")
fl_w = robot.Pose()  # flange in base; world = B * (flange in base frame? robot.Pose() is wrt base frame parent)
print("   flange in-base pos:", ["%.1f" % v for v in fl_w.Pos()])

saved = w.PoseAbs()
w.setPoseAbs(B * transl(0, 100, 0) * B.inv() * saved)
inb = B.inv() * w.PoseAbs()
print("\nwheel pushed, in-base: (%.2f, %.2f, %.2f)" % tuple(v for v in inb.Pos()[:3]))

print("2) RDK.Collision(w, tool)  =", RDK.Collision(w, tool))
print("3) RDK.Collision(robot, w) =", RDK.Collision(robot, w))

print("4) MoveJ_Test, only (tool,wheel) pair ON:")
RDK.setCollisionActive(COLLISION_OFF)
RDK.setCollisionActivePair(COLLISION_ON, tool, w)
r4 = robot.MoveJ_Test(q, q, minstep_deg=1)
print("   ->", r4)

print("5) MoveJ_Test, only (robot,wheel) pair ON:")
RDK.setCollisionActive(COLLISION_OFF)
RDK.setCollisionActivePair(COLLISION_ON, robot, w)
r5 = robot.MoveJ_Test(q, q, minstep_deg=1)
print("   ->", r5)
robot.setJoints(q)

w.setPoseAbs(saved)
RDK.setCollisionActive(COLLISION_ON)
inb2 = B.inv() * w.PoseAbs()
print("\nrestored wheel in-base: (%.2f, %.2f, %.2f)" % tuple(v for v in inb2.Pos()[:3]))
