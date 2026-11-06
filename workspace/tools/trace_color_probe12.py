#!/usr/bin/env python3
"""探针12：Trace 样式设为 Line 后，验证轨迹是否变成默认黄色曲线。"""
import os
import time

from robodk.robolink import Robolink, ITEM_TYPE_ROBOT

RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)
saved_j = robot.Joints().list()[:6]
out = os.path.abspath("_trace_line_style.png")

RDK.Command("Trace", "Line")
RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
RDK.Command("Trace", "On")
q = saved_j[:]
q[0] += 10
robot.MoveJ(q)
q[0] -= 10
robot.MoveJ(q)
time.sleep(0.3)
RDK.Command("Snapshot", out)
print("snapshot:", os.path.exists(out), os.path.getsize(out) if os.path.exists(out) else "")
RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
robot.setJoints(saved_j)
print("恢复:", [round(v, 2) for v in robot.Joints().list()[:6]])
