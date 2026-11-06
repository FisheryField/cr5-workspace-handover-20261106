#!/usr/bin/env python3
"""探针6：用 RoboDK 自带模拟相机拍下 Trace 曲线，判定当前轨迹颜色。
相机挂在参考系上，朝机器人看；Trace On -> 运动 -> 快照 -> 像素分析。
"""
import time

from robodk import robolink as rl
from robodk import robomath

RDK = rl.Robolink()
robot = RDK.Item("", rl.ITEM_TYPE_ROBOT)
frame = RDK.Item("", rl.ITEM_TYPE_FRAME)  # station 基坐标系
print("robot:", robot.Name())

saved_j = robot.Joints().list()[:6]

# 相机放在机器人前方斜上方，看向基座（世界系位姿）
cam_pose = robomath.transl(2500, 0, 1800) * robomath.rotx(robomath.pi * -35 / 180) * robomath.roty(0) * robomath.rotz(robomath.pi)
cam_item = RDK.Cam2D_Add(frame, "FoV=60&Size=1280x960&BgColor=white&NoCrop")
cam_item.setPose(cam_pose)
print("相机已挂:", cam_item.Name())

RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
RDK.Command("Trace", "On")

q = saved_j[:]
for d in (6, -6):
    q = robot.Joints().list()[:6]
    q[0] += d
    robot.MoveJ(q)
time.sleep(0.5)

RDK.Cam2D_Snapshot("_trace_cam1.png", cam_item)
print("快照完成")
RDK.Cam2D_Delete(cam_item)
RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
robot.setJoints(saved_j)
print("恢复完成:", [round(v, 2) for v in robot.Joints().list()[:6]])
