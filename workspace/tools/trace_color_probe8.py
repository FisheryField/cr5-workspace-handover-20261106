#!/usr/bin/env python3
"""探针8：相机跟随 TCP（tool.item 用法），拍 Trace 颜色。"""
import os
import time

from robodk import robolink as rl
from robodk import robomath

RDK = rl.Robolink()
robot = RDK.Item("", rl.ITEM_TYPE_ROBOT)
saved_j = robot.Joints().list()[:6]
out = os.path.abspath("_trace_cam2.png")

# 相机挂到机器人基座参考系，位置固定，但用 lookat 方式构造朝向
frame = RDK.Item("", rl.ITEM_TYPE_FRAME)
# 用 AddMenu 不可靠；直接构造「位于前方、看向基座原点」的位姿
eye = robomath.transl(2400, -1400, 1800)


def lookat_pose(eye_xyz, target_xyz=(0, 0, 400)):
    ex, ey, ez = eye_xyz
    tx, ty, tz = target_xyz
    vx, vy, vz = tx - ex, ty - ey, tz - ez
    hxy = (vx * vx + vy * vy) ** 0.5
    yaw = robomath.atan2(vy, vx)
    pitch = robomath.atan2(vz, hxy)
    # 相机默认朝 +X；先绕 Z 转到目标方位角，再绕本地 Y 抬头
    return robomath.transl(ex, ey, ez) * robomath.rotz(yaw) * robomath.roty(pitch)


cam = RDK.Cam2D_Add(frame, "FoV=60&Size=960x720&BgColor=white")
cam.setPose(lookat_pose((2400, -1400, 1800)))
time.sleep(0.3)

RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
RDK.Command("Trace", "On")
q = saved_j[:]
q[0] += 10
robot.MoveJ(q)
q[0] -= 10
robot.MoveJ(q)
time.sleep(0.4)
RDK.Cam2D_Snapshot(out, cam)
print("snapshot ->", os.path.exists(out), os.path.getsize(out) if os.path.exists(out) else "")
RDK.Cam2D_Close(cam)
RDK.Command("Trace", "Off")
RDK.Command("Trace", "Reset")
robot.setJoints(saved_j)
print("恢复:", [round(v, 2) for v in robot.Joints().list()[:6]])
