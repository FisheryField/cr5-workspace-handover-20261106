#!/usr/bin/env python3
"""探针9：相机挂工具 item（官方典型用法），拍 Trace 颜色。
再对照：工具设为黄色前后各拍一张。
"""
import os
import time

from robodk import robolink as rl

RDK = rl.Robolink()
print("RoboDK version:", RDK.Version())
robot = RDK.Item("", rl.ITEM_TYPE_ROBOT)
tools = RDK.ItemList(rl.ITEM_TYPE_TOOL)
tool = tools[0]
print("tool:", tool.Name())
saved_j = robot.Joints().list()[:6]

out1 = os.path.abspath("_trace_cam3_before.png")
out2 = os.path.abspath("_trace_cam3_after.png")

# 相机挂在工具上，稍微后移让它看到 TCP 前方（沿工具 -X 看回 TCP 方向）
import robodk.robomath as rm
cam = RDK.Cam2D_Add(tool, "FoV=40&Size=800x600")
cam.setPose(rm.transl(-300, 0, 0) * rm.roty(rm.pi))  # 沿 -X 后退并回望
time.sleep(0.3)

RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
RDK.Command("Trace", "On")

q = saved_j[:]
q[0] += 8
robot.MoveJ(q)
q[0] -= 8
robot.MoveJ(q)
time.sleep(0.3)
RDK.Cam2D_Snapshot(out1, cam)
print("before(工具原色) ->", os.path.exists(out1), os.path.getsize(out1))

tool.setColor([1, 1, 0, 1])  # 黄
q[0] += 8
robot.MoveJ(q)
q[0] -= 8
robot.MoveJ(q)
time.sleep(0.3)
RDK.Cam2D_Snapshot(out2, cam)
print("after(工具黄) ->", os.path.exists(out2), os.path.getsize(out2))

RDK.Cam2D_Close(cam)
RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
robot.setJoints(saved_j)
print("恢复:", [round(v, 2) for v in robot.Joints().list()[:6]])
