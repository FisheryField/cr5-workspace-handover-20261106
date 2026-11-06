#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Diag15 (discriminator): new AddFile items default to OFF in the collision
# map? -> import tool STL copy at EXACT overlap with the tool, force the pair
# ON, test. Also copy vs table with pair forced ON.
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")
from robodk.robolink import *
from robodk.robomath import transl

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
tool = RDK.Item('门把手_bs1', ITEM_TYPE_TOOL)
table = RDK.Item('安装台_650x650x80mm', ITEM_TYPE_OBJECT)
B = robot.Parent().PoseAbs()

mesh_world = B * robot.Pose() * tool.GeometryPose()
stl = r"D:\mydata\glm-workplace\tools\diag8_tool_local.stl"
copy = RDK.AddFile(stl)
copy.setName('pair_forced_test')
copy.setPoseAbs(mesh_world)   # exact overlap with the tool mesh
print("copy at exact tool-mesh overlap")

print("1) raw           Collision(copy, tool) = %d" % RDK.Collision(copy, tool))
ret = RDK.setCollisionActivePair(COLLISION_ON, copy, tool)
print("   forced pair ON (ret=%d): Collision(copy, tool) = %d" % (ret, RDK.Collision(copy, tool)))

print("2) copy vs table, pair forced ON, shoved:")
RDK.setCollisionActivePair(COLLISION_ON, copy, table)
tp = table.PoseAbs().Pos(); cp = copy.PoseAbs().Pos()
saved_copy = copy.PoseAbs()
copy.setPoseAbs(transl(tp[0]-cp[0], tp[1]-cp[1], 40.0-cp[2]) * saved_copy)
print("   Collision(copy, table) = %d  (1 expected)" % RDK.Collision(copy, table))

# 3) original wheel deep-push with BOTH forced orders + global ON (last try)
w = RDK.Item('磨砂圆柱_R180_H40', ITEM_TYPE_OBJECT)
RDK.setCollisionActivePair(COLLISION_ON, w, copy)
print("3) wheel(during copy test) vs copy ON-check: Collision(w, copy) = %d" % RDK.Collision(w, copy))

copy.Delete()
print("\n(copy deleted; wheel untouched this run)")
