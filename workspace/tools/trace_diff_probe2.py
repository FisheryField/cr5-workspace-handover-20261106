#!/usr/bin/env python3
"""探针14：Trace 显示 vs Reset 清除 差分 → 轨迹本体像素。"""
import os
import time

from robodk.robolink import Robolink, ITEM_TYPE_ROBOT

RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)
a = os.path.abspath("_trace_on.png")
b = os.path.abspath("_trace_cleared.png")

saved_j = robot.Joints().list()[:6]
RDK.Command("Trace", "Line")
RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
RDK.Command("Trace", "On")
q = saved_j[:]
q[0] += 12
robot.MoveJ(q)
q[0] -= 12
robot.MoveJ(q)
time.sleep(0.4)
RDK.Command("Snapshot", a)
time.sleep(0.3)
RDK.Command("Trace", "Reset")   # 清除已画轨迹
time.sleep(0.5)
RDK.Command("Snapshot", b)
print("on:", os.path.getsize(a), "cleared:", os.path.getsize(b))
