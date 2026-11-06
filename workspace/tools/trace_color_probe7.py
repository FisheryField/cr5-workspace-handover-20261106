#!/usr/bin/env python3
"""探针7：Cam2D_Snapshot 用绝对路径；先拍一张验证可行性。"""
import os
import time

from robodk import robolink as rl
from robodk import robomath

RDK = rl.Robolink()
robot = RDK.Item("", rl.ITEM_TYPE_ROBOT)
frame = RDK.Item("", rl.ITEM_TYPE_FRAME)
saved_j = robot.Joints().list()[:6]

out = os.path.abspath("_trace_cam1.png")
cam_item = RDK.Cam2D_Add(frame, "FoV=60&Size=960x720&BgColor=white")
cam_pose = robomath.transl(2600, 0, 1900) * robomath.rotx(robomath.pi * -33 / 180) * robomath.rotz(robomath.pi)
cam_item.setPose(cam_pose)

RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
RDK.Command("Trace", "On")
q = robot.Joints().list()[:6]
q[0] += 10
robot.MoveJ(q)
q[0] -= 10
robot.MoveJ(q)
time.sleep(0.4)
RDK.Cam2D_Snapshot(out, cam_item)
print("snapshot ->", out, os.path.exists(out), os.path.getsize(out) if os.path.exists(out) else "")
RDK.Cam2D_Close(cam_item)
RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
robot.setJoints(saved_j)
print("恢复:", [round(v, 2) for v in robot.Joints().list()[:6]])
