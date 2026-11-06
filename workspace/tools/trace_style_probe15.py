#!/usr/bin/env python3
"""探针15：切换 Trace_Render_Style 后差分验证轨迹渲染样式。
测试顺序：读当前值 -> 尝试 setParam 4(Line 猜测) -> On/Off 循环 -> 差分统计颜色。"""
import os
import time

from robodk.robolink import Robolink, ITEM_TYPE_ROBOT

RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)
saved_j = robot.Joints().list()[:6]

try:
    print("getParam Trace_Render_Style:", RDK.getParam("Trace_Render_Style"))
except Exception as e:
    print("getParam fail:", e)

# 尝试设置样式 4（References/Points/Spheres/Dots/Line -> 0..4）
RDK.setParam("Trace_Render_Style", "4")
try:
    print("after set:", RDK.getParam("Trace_Render_Style"))
except Exception as e:
    print("getParam fail:", e)

a = os.path.abspath("_trace_style4_on.png")
b = os.path.abspath("_trace_style4_cleared.png")
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
RDK.Command("Trace", "Reset")
time.sleep(0.5)
RDK.Command("Snapshot", b)
print("shots:", os.path.getsize(a), os.path.getsize(b))
RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
