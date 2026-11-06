#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Read-only: which station is this, item inventory, wheel pose relative to
# ROBOT BASE frame, flange vs TCP distinction.
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")
from robodk.robolink import *
from robodk.robomath import *

RDK = Robolink()
act = RDK.ActiveStation()
print("active station:", act.Name())

print("\n--- item inventory ---")
for it in RDK.ItemList():
    try:
        print("  [%d] %s" % (it.type(), it.Name()))
    except Exception:
        pass

robot = RDK.Item('', ITEM_TYPE_ROBOT)
base = robot.Parent()
print("\nrobot parent (base):", base.Name() if base.Valid() else "(root)")
bp = base.PoseAbs()
print("base PoseAbs pos:", ["%.3f" % v for v in bp.Pos()])
print("base PoseAbs rows:")
for r in bp.rows[:3]:
    print("   ", ["%8.4f" % v for v in r[:3]])

w = RDK.Item('磨砂圆柱_R180_H40', ITEM_TYPE_OBJECT)
gl = w.GeometryPose()   # pose relative to parent
print("\nwheel GeometryPose (parent-relative): pos", ["%.3f" % v for v in gl.Pos()])
bp_inv = bp.inv()
w_in_base = bp_inv * w.PoseAbs()
print("wheel in BASE frame: pos", ["%.3f" % v for v in w_in_base.Pos()])
print("wheel in BASE frame rows:")
for r in w_in_base.rows[:3]:
    print("   ", ["%8.4f" % v for v in r[:3]])

print("\nrobot PoseTool:\n", robot.PoseTool())
flange = robot.Pose()
print("flange pose (Fanuc): [%.2f, %.2f, %.2f, %.2f, %.2f, %.2f]" % tuple(Pose_2_Fanuc(flange)))
tcp = flange * robot.PoseTool()
print("TCP (Fanuc):          [%.2f, %.2f, %.2f, %.2f, %.2f, %.2f]" % tuple(Pose_2_Fanuc(tcp)))
