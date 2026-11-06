#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Read-only facts: open stations, wheel world pose, table pose, arm current TCP.
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")
from robodk.robolink import *
from robodk.robomath import *

RDK = Robolink()
print("RoboDK connected")

try:
    sts = RDK.ItemList(ITEM_TYPE_STATION, False)
    names = [s.Name() for s in sts] if isinstance(sts, list) else [str(sts)]
    print("stations open:", names)
except Exception as e:
    print("station list err:", e)
try:
    act = RDK.ActiveStation()
    print("active station:", act.Name() if act.Valid() else "(none)")
except Exception as e:
    print("ActiveStation err:", e)

robot = RDK.Item('', ITEM_TYPE_ROBOT)
print("robot:", robot.Name(), "valid:", robot.Valid())

w = RDK.Item('磨砂圆柱_R180_H40', ITEM_TYPE_OBJECT)
print("wheel valid:", w.Valid())
if w.Valid():
    pa = w.PoseAbs()
    print("wheel PoseAbs pos:", ["%.3f" % v for v in pa.Pos()])
    print("wheel PoseAbs rot rows:")
    for r in pa.rows[:3]:
        print("   ", ["%8.4f" % v for v in r[:3]])
    par = w.Parent()
    print("wheel parent:", par.Name() if par.Valid() else "(root)")

t = RDK.Item('安装台_650x650x80mm', ITEM_TYPE_OBJECT)
if t.Valid():
    print("table PoseAbs pos:", ["%.2f" % v for v in t.PoseAbs().Pos()])

tool = RDK.Item('门把手_bs1', ITEM_TYPE_TOOL)
print("tool valid:", tool.Valid())

j = robot.Joints().list()[:6]
print("arm joints now:", ["%.3f" % v for v in j])
tcp = robot.Pose() * robot.PoseTool()
print("arm TCP now (Fanuc): [%.2f, %.2f, %.2f, %.2f, %.2f, %.2f]" % tuple(Pose_2_Fanuc(tcp)))
