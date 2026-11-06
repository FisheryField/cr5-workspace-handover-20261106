#!/usr/bin/env python3
"""探针20：验证「AddCurve + 黄色」能画出肉眼可见的黄色 TCP 轨迹曲线。
步骤：取活动工具 -> 小幅运动记录 5 个 TCP 世界坐标 -> AddCurve -> 染黄 -> 截图 -> 关节复原。
"""
import os
import time

from robodk.robolink import Robolink, ITEM_TYPE_ROBOT, ITEM_TYPE_TOOL, PROJECTION_NONE
from robodk import robomath

RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)
tool = robot.getLink(ITEM_TYPE_TOOL)
print("tool via getLink:", tool.Name() if tool.Valid() else "(invalid)")

saved_j = robot.Joints().list()[:6]
pts = [tool.PoseAbs().Pos()]
RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
for d in (6, -3, -6, 3):
    q = robot.Joints().list()[:6]
    q[0] += d
    robot.MoveJ(q)
    pts.append(tool.PoseAbs().Pos())
print("记录点:", [(round(p[0], 1), round(p[1], 1), round(p[2], 1)) for p in pts])

mat = robomath.Mat([list(p) for p in pts]).tr()
curve = RDK.AddCurve(mat, None, False, PROJECTION_NONE)
curve.setName("_探针_黄曲线测试")
curve.setColorCurve([1.0, 0.82, 0.0, 1.0])
print("curve:", curve.Name(), curve.Valid())
time.sleep(0.4)
out = os.path.abspath("_probe20_curve.png")
RDK.Command("Snapshot", out)
print("snapshot:", os.path.getsize(out))
robot.setJoints(saved_j)
print("关节复原:", [round(v, 2) for v in robot.Joints().list()[:6]])
