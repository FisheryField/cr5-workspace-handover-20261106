#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Diag10: during a wheel-engulf of the tool rod, test if the PAIR MAP is the
# culprit: dump CollisionActivePairList entries involving wheel/tool/robot,
# then compare RDK.Collision(tool,w) before/after forcing the pair ON.
# Exact restore at the end. No joint moves.
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")
from robodk.robolink import *

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
w = RDK.Item('磨砂圆柱_R180_H40', ITEM_TYPE_OBJECT)
tool = RDK.Item('门把手_bs1', ITEM_TYPE_TOOL)

print("--- robot children / attachments ---")
try:
    for c in robot.Childs():
        print("   child:", c.Name())
except Exception as e:
    print("   Childs err:", e)

print("\n--- CollisionActivePairList (map config) ---")
try:
    lst = RDK.CollisionActivePairList()
    print("entries:", len(lst))
    for a, b, st, sid in lst:
        try:
            na, nb = a.Name(), b.Name()
            if ('磨砂' in na or '磨砂' in nb or 'Dobot' in na or 'Dobot' in nb
                    or '把手' in na or '把手' in nb):
                print("   %-28s <-> %-28s state=%s" % (na[:28], nb[:28], st))
        except Exception:
            pass
except Exception as e:
    print("CollisionActivePairList err:", e)

# engulf the rod
from robodk.robomath import transl
B = robot.Parent().PoseAbs()
saved = w.PoseAbs()
rod_world = (B * transl(179.6, -774.8, 300.0)).Pos()
w.setPoseAbs(transl(rod_world[0]-saved.Pos()[0], rod_world[1]-saved.Pos()[1],
                    rod_world[2]-saved.Pos()[2]) * saved)
print("\n--- during engulf, Collision(tool, wheel) ---")
print("map default            :", RDK.Collision(tool, w))
RDK.setCollisionActivePair(COLLISION_ON, tool, w)
print("after pair forced ON   :", RDK.Collision(tool, w))
RDK.setCollisionActivePair(COLLISION_ON, robot, w)
print("robot pair forced ON   :", RDK.Collision(robot, w))
RDK.setCollisionActive(COLLISION_ON)
print("global all-ON          :", RDK.Collision(tool, w), "/", RDK.Collision(robot, w))

w.setPoseAbs(saved)
print("\nrestored wheel in-base: (%.2f, %.2f, %.2f)"
      % tuple(v for v in (B.inv()*w.PoseAbs()).Pos()[:3]))
