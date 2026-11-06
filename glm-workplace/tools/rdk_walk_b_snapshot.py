#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""走 B 方案并用 API SnapShot 抓 3D 视图（不动脚本、不连真机）。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from robodk import robolink, robomath

RDK = robolink.Robolink()
robot = RDK.Item("Dobot CR5", robolink.ITEM_TYPE_ROBOT)

state_raw = robot.ConnectedState()
state = state_raw[0] if isinstance(state_raw, tuple) else state_raw
print("ConnectedState =", state_raw)
if state not in (robolink.ROBOTCOM_DISCONNECTED, robolink.ROBOTCOM_NOT_CONNECTED, -1, 0, None):
    print("ABORT: 已连真机"); sys.exit(2)
RDK.setRunMode(robolink.RUNMODE_SIMULATE)

def report(tag):
    p = robot.Pose()
    T = p
    zcol = [T[0, 2], T[1, 2], T[2, 2]]
    tcp = [T[0, 3], T[1, 3], T[2, 3]]
    fn = [tcp[k] - 12.3 * zcol[k] for k in range(3)]
    fp = [tcp[k] + 12.3 * zcol[k] for k in range(3)]
    print("[%s] TCP=(%.2f, %.2f, %.2f)  -Z面=(%.2f, %.2f, %.2f) gap=%.2f  +Z面=(%.2f, %.2f, %.2f) gap=%.2f" % (
        tag, tcp[0], tcp[1], tcp[2], fn[0], fn[1], fn[2], fn[1] + 776, fp[0], fp[1], fp[2], fp[1] + 776))

# B 方案
poseB = robomath.xyzrpw_2_pose([0, -762.7, 300, 90, 0, 0])
robot.MoveJ(poseB, blocking=True)
report("B (90,0,0)")
print("关节:", [round(x, 3) for x in robot.Joints().list()])

# 抓 3D 视图快照
for arg in (r"D:\mydata\glm-workplace\data\screens\rdk_view_B.png",):
    try:
        res = RDK.Command("SnapShot", arg)
        print("SnapShot:", res)
    except Exception as e:
        print("SnapShot fail:", e)

# 回 A 方案再抓一张
poseA = robomath.xyzrpw_2_pose([0, -762.7, 300, -90, 0, 180])
robot.MoveJ(poseA, blocking=True)
report("A (-90,0,180)")
print("关节:", [round(x, 3) for x in robot.Joints().list()])
try:
    res = RDK.Command("SnapShot", r"D:\mydata\glm-workplace\data\screens\rdk_view_A.png")
    print("SnapShot:", res)
except Exception as e:
    print("SnapShot fail:", e)
