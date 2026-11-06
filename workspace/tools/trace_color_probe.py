#!/usr/bin/env python3
"""探针：查 RoboDK Trace 对象的真名/类型/颜色与 setColor 可行性。
只动仿真模型，结束后恢复关节。为「实际运行轨迹改成默认黄色」任务铺路。
"""
import time

from robodk.robolink import *
from robodk.robomath import *

RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)
q0 = robot.Joints().list()[:6]
print("起始关节:", [round(v, 3) for v in q0])

# Trace On → 小幅运动 → 找 Trace 对象
RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
RDK.Command("Trace", "On")
target = q0[:]
target[0] += 8.0
robot.MoveJ(target)
time.sleep(0.5)

print("\n--- 站内全部对象 ---")
for it in RDK.ItemList():
    try:
        print("  %-28s type=%d" % (it.Name(), int(it.Type())))
    except Exception as e:
        print("  ? %s" % e)

trace = None
for name in ("Trace", "TCP Trace", "轨迹"):
    cand = RDK.Item(name, ITEM_TYPE_OBJECT)
    if cand.Valid():
        trace = cand
        print("\n找到 Trace 对象: %r type=%d" % (cand.Name(), int(cand.Type())))
        break

if trace is not None and trace.Valid():
    try:
        print("当前颜色 Color():", [round(c, 3) for c in trace.Color()])
    except Exception as e:
        print("Color() 失败:", e)
    try:
        trace.setColor([1.0, 0.8, 0.0])  # 黄色 (RGB 255,204,0)
        print("setColor([1,0.8,0]) 调用成功；回读:", [round(c, 3) for c in trace.Color()])
    except Exception as e:
        print("setColor 失败:", e)

RDK.Command("Trace", "Off")
robot.setJoints(q0)
print("\n关节已恢复:", [round(v, 3) for v in robot.Joints().list()[:6]])
