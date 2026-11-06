#!/usr/bin/env python3
"""探针33：D = actual*inv(FK*tool) 在多个构型下是否恒定？
恒定 => 纯变换差，可离线重建；变化 => FK 模型与显示模型不一致。
"""
import time

from robodk import robomath
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT, ITEM_TYPE_TOOL

RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)
tool = robot.getLink(ITEM_TYPE_TOOL)
tool_pose = tool.PoseTool()
base = robot.PoseAbs()

saved = robot.Joints().list()[:6]


def report(tag):
    q = robot.Joints().list()[:6]
    actual = tool.PoseAbs()
    D = actual * robomath.invH(robot.SolveFK(q) * tool_pose)
    xyzrpy = robomath.pose_2_xyzrpw(D)
    print("%-10s D.Pos=[%8.2f %8.2f %8.2f] rpy=[%6.2f %6.2f %6.2f]"
          % (tag, xyzrpy[0], xyzrpy[1], xyzrpy[2], xyzrpy[3], xyzrpy[4], xyzrpy[5]))
    return D


report("原位")
for d1, d2 in ((15, 0), (15, -10), (-30, 20), (0, -25), (25, 15)):
    q = list(saved)
    q[0] += d1
    q[2] += d2
    robot.MoveJ(q)
    time.sleep(0.15)
    report("d=%+d,%+d" % (d1, d2))

robot.MoveJ(saved)
time.sleep(0.15)
report("复原")
print("关节:", [round(v, 2) for v in robot.Joints().list()[:6]])
