#!/usr/bin/env python3
"""探针3：验证 RoboDK TCP Trace 曲线颜色是否跟随工具颜色。
方法：Trace On -> 工具设黄色 -> 运动；截图 A。再设洋红 -> 运动；截图 B。
肉眼/图像判断曲线颜色是否变化。结束恢复关节与工具颜色、关 Trace。
"""
import time

from robodk.robolink import *  # noqa: F401,F403

RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)
tools = RDK.ItemList(ITEM_TYPE_TOOL)
tool = RDK.Item(str(tools[0]), ITEM_TYPE_TOOL) if tools else None
print("robot:", robot.Name(), "| 工具列表:", tools)

saved_j = robot.Joints().list()[:6]
orig_color = tool.getColor() if tool and tool.Valid() else None
print("工具原色:", orig_color)

RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
RDK.Command("Trace", "On")

def wiggle():
    q = saved_j[:]
    q[0] += 6.0
    robot.MoveJ(q)
    q[0] -= 6.0
    robot.MoveJ(q)

if tool and tool.Valid():
    tool.setColor([1, 1, 0, 1])   # 黄
    wiggle()
    time.sleep(0.5)
    ok1 = RDK.Screenshot("_trace_yellow.png") if hasattr(RDK, "Screenshot") else None
    print("黄色段截图:", ok1)

    tool.setColor([1, 0, 1, 1])   # 洋红
    wiggle()
    time.sleep(0.5)
    ok2 = RDK.Screenshot("_trace_magenta.png") if hasattr(RDK, "Screenshot") else None
    print("洋红段截图:", ok2)

    if orig_color is not None:
        tool.setColor(orig_color)
        print("工具色已恢复")

RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
robot.setJoints(saved_j)
print("关节已恢复:", [round(v, 2) for v in robot.Joints().list()[:6]])
