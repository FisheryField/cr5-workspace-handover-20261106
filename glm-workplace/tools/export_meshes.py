#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Read-only: (1) read CURRENT TCP pose (user manually posed the arm - anchor!),
# (2) export 门把手_bs1 and 磨砂圆柱 meshes to STL in workspace tools/.
# No joint moves, no station changes.
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")
from robodk.robolink import *
from robodk.robomath import *

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
toolT = RDK.Item('门把手_bs1', ITEM_TYPE_TOOL)

# current pose (info only)
pose = robot.Pose() * toolT.PoseTool()   # TCP pose in base frame (approx, tool=transl)
print("current joints :", ["%.3f" % v for v in robot.Joints().list()[:6]])
fv = Pose_2_Fanuc(pose)
print("current TCP (Fanuc xyzwpr): [%.2f, %.2f, %.2f, %.3f, %.3f, %.3f]" % tuple(fv))

out_dir = r"D:\mydata\glm-workplace\tools"
os.makedirs(out_dir, exist_ok=True)
for item, fn in ((toolT, "handle_bs1.stl"),):
    dst = os.path.join(out_dir, fn)
    try:
        res = RDK.Save(dst, item)
        print("saved:", dst, "->", res)
    except Exception as e:
        print("Save err:", type(e).__name__, e)

wheel = RDK.Item('磨砂圆柱_R180_H40', ITEM_TYPE_OBJECT)
if wheel.Valid():
    dst = os.path.join(out_dir, "wheel_R180_H40.stl")
    try:
        res = RDK.Save(dst, wheel)
        print("saved:", dst, "->", res)
    except Exception as e:
        print("Save wheel err:", type(e).__name__, e)

for fn in ("handle_bs1.stl", "wheel_R180_H40.stl"):
    p = os.path.join(out_dir, fn)
    if os.path.exists(p):
        print(fn, os.path.getsize(p), "bytes")
