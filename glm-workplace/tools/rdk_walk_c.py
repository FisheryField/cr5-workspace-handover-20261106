#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""走 C 方案（-Z 面贴轮：90,0,180 与 -90,0,0 两个臂向）+ 快照 + 回原位。"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from robodk import robolink, robomath

RDK = robolink.Robolink()
robot = RDK.Item("Dobot CR5", robolink.ITEM_TYPE_ROBOT)
state_raw = robot.ConnectedState()
state = state_raw[0] if isinstance(state_raw, tuple) else state_raw
if state not in (robolink.ROBOTCOM_DISCONNECTED, robolink.ROBOTCOM_NOT_CONNECTED, -1, 0, None):
    print("ABORT: 已连真机"); sys.exit(2)
RDK.setRunMode(robolink.RUNMODE_SIMULATE)

def report(tag):
    T = robot.Pose()
    zcol = [T[0, 2], T[1, 2], T[2, 2]]
    tcp = [T[0, 3], T[1, 3], T[2, 3]]
    fn = [tcp[k] - 12.3 * zcol[k] for k in range(3)]
    fp = [tcp[k] + 12.3 * zcol[k] for k in range(3)]
    ycol = [T[0, 1], T[1, 1], T[2, 1]]
    neck_tip = [tcp[k] + 59.5 * ycol[k] for k in range(3)]
    print("[%s] TCP=(%.1f,%.1f,%.1f) -Z面y=%.2f gap=%.2f | +Z面y=%.2f gap=%.2f | 颈尖=(%.0f,%.0f,%.0f)" % (
        tag, tcp[0], tcp[1], tcp[2], fn[1], fn[1] + 776, fp[1], fp[1] + 776,
        neck_tip[0], neck_tip[1], neck_tip[2]))

for tag, wpr in [("C1 (90,0,180) -Z面/臂-X", [0, -762.7, 300, 90, 0, 180]),
                 ("C2 (-90,0,0) -Z面/臂+X", [0, -762.7, 300, -90, 0, 0])]:
    pose = robomath.xyzrpw_2_pose(wpr)
    robot.MoveJ(pose, blocking=True)
    report(tag)
    print("  关节:", [round(x, 3) for x in robot.Joints().list()])

RDK.Command("SnapShot", r"D:\mydata\glm-workplace\data\screens\rdk_view_C.png")

# 回原位
j0 = json.load(open(r"D:\mydata\glm-workplace\data\scripts_ref\sim_walk_j0.json", encoding="utf-8"))
robot.MoveJ(j0, blocking=True)
print("已回原位, 关节:", [round(x, 3) for x in robot.Joints().list()])
RDK.Command("SnapShot", r"D:\mydata\glm-workplace\data\screens\rdk_view_home.png")
print("done")
