#!/usr/bin/env python3
"""探针2：Trace 前后列出全部 item（不过滤类型），找出 Trace 载体。"""
import time

from robodk.robolink import *  # noqa: F401,F403

RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)

def snap():
    names = RDK.ItemList()
    return {n: i for i, n in enumerate(names)}

before = snap()
saved = robot.Joints().list()[:6]
RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
RDK.Command("Trace", "On")
q = saved[:]
q[0] += 8.0
robot.MoveJ(q)
q[0] -= 8.0
robot.MoveJ(q)
time.sleep(0.8)
after = snap()
new = {n: i for n, i in after.items() if n not in before}
print("全部 item 数: %d -> %d" % (len(before), len(after)))
print("新增:", new if new else "（无）")
# 逐个类型尝试按名取 Trace
for t, tname in ((ITEM_TYPE_OBJECT, "OBJECT"), (ITEM_TYPE_CURVE, "CURVE"),
                 (ITEM_TYPE_ROBOT, "ROBOT"), (ITEM_TYPE_TOOL, "TOOL"), (-1, "ANY")):
    it = RDK.Item("Trace", t)
    print("Item('Trace', %s).Valid() = %s" % (tname, it.Valid()))
RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
robot.setJoints(saved)
print("restored:", [round(v, 2) for v in robot.Joints().list()[:6]])
