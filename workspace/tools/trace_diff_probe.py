#!/usr/bin/env python3
"""探针13：Trace On/Off 差分，提取轨迹本体像素并统计颜色。
不动机器人（保持同一姿态），两次快照之间只切换 Trace 显示。"""
import os
import time

from robodk.robolink import Robolink, ITEM_TYPE_ROBOT

RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)
# 不保存/恢复：保持当前姿态完全不动
a = os.path.abspath("_trace_on.png")
b = os.path.abspath("_trace_off.png")

# 先做一段运动产生轨迹，然后停在起点
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
RDK.Command("Trace", "Off")
time.sleep(0.4)
RDK.Command("Snapshot", b)
print("on:", os.path.getsize(a), "off:", os.path.getsize(b))
RDK.Command("Trace", "Reset")
