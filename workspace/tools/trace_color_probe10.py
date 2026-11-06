#!/usr/bin/env python3
"""探针10：RDK.Command('Snapshot') 截 3D 主视图，判定 Trace 颜色。"""
import os
import time

from robodk.robolink import Robolink, ITEM_TYPE_ROBOT

RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)
saved_j = robot.Joints().list()[:6]

out1 = os.path.abspath("_trace_snap1.png")

RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
RDK.Command("Trace", "On")
q = saved_j[:]
q[0] += 10
robot.MoveJ(q)
q[0] -= 10
robot.MoveJ(q)
time.sleep(0.3)
# Snapshot: name=文件名, path可选; 传绝对路径
res = RDK.Command("Snapshot", out1)
print("Snapshot result:", res)
print("exists:", os.path.exists(out1), os.path.getsize(out1) if os.path.exists(out1) else "")
RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
robot.setJoints(saved_j)
print("恢复:", [round(v, 2) for v in robot.Joints().list()[:6]])
