#!/usr/bin/env python3
"""探针30：差修正法重建 TCP 世界坐标。
corr = tool.PoseAbs() * inv(base*FK(q0)*tool_pose)   在 q0 标定一次；
任意 q 的 TCP 世界位姿 = corr * base * FK(q) * tool_pose。
用 MoveJ 到两个不同关节实测 PoseAbs 对照，偏差应 < 0.01mm。
"""
import time

from robodk import robomath
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT, ITEM_TYPE_TOOL

RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)
tool = robot.getLink(ITEM_TYPE_TOOL)

q0 = robot.Joints().list()[:6]
base_pose = robot.PoseAbs()
tool_pose = tool.PoseTool()
corr = tool.PoseAbs() * robomath.invH(base_pose * robot.SolveFK(q0) * tool_pose)
print("corr:", [round(v, 3) for v in corr.Pos()], "（应≈0,0,0 若基座无偏差）")


def tcp_world(q):
    return (corr * base_pose * robot.SolveFK(q) * tool_pose).Pos()


saved = list(q0)
worst = 0.0
for d1 in (15.0, -30.0, 20.0):
    q = list(saved)
    q[0] += d1
    q[2] -= d1 / 2
    robot.MoveJ(q)
    time.sleep(0.2)
    actual = tool.PoseAbs().Pos()
    pred = tcp_world(robot.Joints().list()[:6])
    dev = max(abs(a - b) for a, b in zip(actual, pred))
    worst = max(worst, dev)
    print("q[0]%+.0f: 实测%s 预测%s 偏差 %.4f mm" % (d1, [round(v, 1) for v in actual], [round(v, 1) for v in pred], dev))

robot.MoveJ(saved)
time.sleep(0.2)
actual = tool.PoseAbs().Pos()
pred = tcp_world(robot.Joints().list()[:6])
print("回到原位 偏差 %.4f mm" % max(abs(a - b) for a, b in zip(actual, pred)))
print("worst = %.4f mm ->%s" % (worst, "PASS" if worst < 0.01 else "FAIL"))
