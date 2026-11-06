#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Diag11: during engulf, force the (tool,wheel)/(robot,wheel) pair ON for
# every link id 0..7 and both argument orders. Report which (if any) fires.
# Exact restore. No joint moves.
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")
from robodk.robolink import *
from robodk.robomath import transl

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
w = RDK.Item('磨砂圆柱_R180_H40', ITEM_TYPE_OBJECT)
tool = RDK.Item('门把手_bs1', ITEM_TYPE_TOOL)
B = robot.Parent().PoseAbs()

saved = w.PoseAbs()
rod_world = (B * transl(179.6, -774.8, 300.0)).Pos()
w.setPoseAbs(transl(rod_world[0]-saved.Pos()[0], rod_world[1]-saved.Pos()[1],
                    rod_world[2]-saved.Pos()[2]) * saved)
print("engulfed; baseline Collision(tool,w) =", RDK.Collision(tool, w))

hit = []
for i in range(8):
    r1 = RDK.setCollisionActivePair(COLLISION_ON, tool, w, i, 0)
    c1 = RDK.Collision(tool, w)
    r2 = RDK.setCollisionActivePair(COLLISION_ON, w, tool, 0, i)
    c2 = RDK.Collision(w, tool)
    print("id=%d  (tool,w,%d,0)=%d -> %d   (w,tool,0,%d)=%d -> %d"
          % (i, i, r1, c1, i, r2, c2))
    if c1 or c2:
        hit.append(i)

print("\nlink ids that fired:", hit if hit else "NONE")

for i in range(7):
    RDK.setCollisionActivePair(COLLISION_ON, robot, w, i, 0)
print("robot all-links forced ON: Collision(robot,w) =", RDK.Collision(robot, w))

# B-plan preview: fresh import of the wheel STL as a NEW object, same pose
import os
stl = r"D:\mydata\glm-workplace\tools\wheel_R180_H40.stl"
if os.path.exists(stl):
    copy = RDK.AddFile(stl)
    copy.setName('磨砂圆柱_验证副本')
    copy.setPoseAbs(saved)   # target pose directly (not the engulf pose)
    inb = B.inv() * copy.PoseAbs()
    print("\nB-plan: fresh wheel copy at in-base (%.2f, %.2f, %.2f)"
          % tuple(v for v in inb.Pos()[:3]))
    print("   Collision(tool, copy) at TARGET pose (delta=5mm) =", RDK.Collision(tool, copy))
    print("   Collision(robot, copy) =", RDK.Collision(robot, copy))
    # engulf the copy too for positive control
    copy.setPoseAbs(transl(rod_world[0]-saved.Pos()[0], rod_world[1]-saved.Pos()[1],
                           rod_world[2]-saved.Pos()[2]) * saved)
    print("   engulfed: Collision(tool, copy) =", RDK.Collision(tool, copy))
    copy.Delete()
    print("   (copy deleted)")
else:
    print("\nB-plan skipped: STL not found at", stl)

w.setPoseAbs(saved)
print("\nrestored wheel in-base: (%.2f, %.2f, %.2f)"
      % tuple(v for v in (B.inv()*w.PoseAbs()).Pos()[:3]))
