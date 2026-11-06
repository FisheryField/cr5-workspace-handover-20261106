# -*- coding: utf-8 -*-
"""只读：读站内所有目标点（Pose）与机器人当前关节，找 (-90,0,0) 示教点。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import *
from robodk.robomath import *

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)

print('=== 目标点 ===')
for it in RDK.ItemList(ITEM_TYPE_TARGET):
    P = it.Pose()
    f = Pose_2_Fanuc(P)
    parent = it.Parent().Name()
    print('%-10s parent=%-14s xyz=(%.3f, %.3f, %.3f) Fanuc=(%.3f, %.3f, %.3f)' % (
        it.Name(), parent, f[0], f[1], f[2], f[3], f[4], f[5]))

print('=== 机器人当前 ===')
q = robot.Joints().list()
print('Joints =', ['%.3f' % v for v in q])
TCP = robot.SolveFK(robot.Joints()) * robot.PoseTool()
f = Pose_2_Fanuc(TCP)
print('TCP xyz=(%.3f, %.3f, %.3f) Fanuc=(%.3f, %.3f, %.3f)' % (f[0], f[1], f[2], f[3], f[4], f[5]))
