# -*- coding: utf-8 -*-
"""只读：读站内机器人当前关节 → FK → TCP(FK·PoseTool) → Fanuc 角，确认当前末端姿态是否 (-90,0,0)。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import *
from robodk.robomath import *

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
if not robot.Valid():
    raise SystemExit('未找到机器人')
q = robot.Joints().list()
print('Joints =', ['%.3f' % v for v in q])
FK = robot.SolveFK(robot.Joints())
print('FK 法兰 base xyz = (%.3f, %.3f, %.3f)' % (FK[0, 3], FK[1, 3], FK[2, 3]))
print('FK 法兰 Fanuc =', ['%.3f' % v for v in Pose_2_Fanuc(FK)])
PT = robot.PoseTool()
print('PoseTool =', ['%.3f' % v for v in Pose_2_Fanuc(PT)])
PF = robot.PoseFrame()
print('PoseFrame =', ['%.3f' % v for v in Pose_2_Fanuc(PF)])
TCP = FK * PT
print('TCP base xyz = (%.3f, %.3f, %.3f)' % (TCP[0, 3], TCP[1, 3], TCP[2, 3]))
print('TCP Fanuc =', ['%.3f' % v for v in Pose_2_Fanuc(TCP)])
# 工具 z 轴在 base 系方向
tz = [TCP[0, 2], TCP[1, 2], TCP[2, 2]]
print('TCP z轴 base 方向 = (%.3f, %.3f, %.3f)' % tuple(tz))
