#!/usr/bin/env python3
"""探针11：A/B 实验——工具原色 vs 工具染黄，各截一张，验证 Trace 颜色是否跟随工具色。"""
import os
import time

from robodk.robolink import Robolink, ITEM_TYPE_ROBOT, ITEM_TYPE_TOOL

RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)
tools = RDK.ItemList(ITEM_TYPE_TOOL)
tool = tools[0]
print("tool:", tool.Name())
saved_j = robot.Joints().list()[:6]

outA = os.path.abspath("_trace_A_default.png")
outB = os.path.abspath("_trace_B_toolyellow.png")

def move_and_snap(path, tag):
    RDK.Command("Trace", "Off")
    RDK.Command("Trace", "Reset")
    RDK.Command("Trace", "On")
    q = saved_j[:]
    q[0] += 10
    robot.MoveJ(q)
    q[0] -= 10
    robot.MoveJ(q)
    time.sleep(0.3)
    RDK.Command("Snapshot", path)
    print(tag, "->", os.path.exists(path), os.path.getsize(path) if os.path.exists(path) else "")

move_and_snap(outA, "A(工具原色)")

tool.setColor([1, 1, 0, 1])  # 黄色
move_and_snap(outB, "B(工具黄)")

RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
robot.setJoints(saved_j)
print("恢复关节:", [round(v, 2) for v in robot.Joints().list()[:6]])
print("提示：工具颜色仍为黄色，如需还原请观察后处理")
