#!/usr/bin/env python3
"""探针17：单独验证 Command('Trace','Line') 之后，Reset 是否还能清掉轨迹。
如果 On/Reset 差分为 0，说明 Line 样式的轨迹不是'逐帧参考架'，而是持久几何，
或者 Reset 之后轨迹立刻重新被画（机器人静止不动）。
方案：运动产生轨迹 -> 截图 A -> Reset -> 截图 B -> 再运动一点 -> 截图 C。
B==A 则 Reset 没清掉；C 与 B 差分 = 新增轨迹。"""
import os
import time

from robodk.robolink import Robolink, ITEM_TYPE_ROBOT

RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)
saved_j = robot.Joints().list()[:6]
A = os.path.abspath("_t17_A.png")
B = os.path.abspath("_t17_B.png")
C = os.path.abspath("_t17_C.png")

RDK.Command("Trace", "Line")
RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
RDK.Command("Trace", "On")
q = saved_j[:]
q[0] += 12
robot.MoveJ(q)
q[0] -= 12
robot.MoveJ(q)
time.sleep(0.5)
RDK.Command("Snapshot", A)
RDK.Command("Trace", "Reset")
time.sleep(0.6)
RDK.Command("Snapshot", B)
q[0] += 6
robot.MoveJ(q)
time.sleep(0.5)
RDK.Command("Snapshot", C)
RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
robot.setJoints(saved_j)
print("done", os.path.getsize(A), os.path.getsize(B), os.path.getsize(C))
