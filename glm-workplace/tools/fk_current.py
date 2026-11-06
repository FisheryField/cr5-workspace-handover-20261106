#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 只读：FK当前关节 -> TCP；并对比几个关键位姿
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")
from robodk.robolink import *
from robodk.robomath import *

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
q = robot.Joints().list()[:6]
print("current joints:", ["%.3f" % v for v in q])
tcp = invH(robot.PoseFrame()) * robot.SolveFK(q) * robot.PoseTool()
p = tcp.Pos()
r = Pose_2_Fanuc(tcp)
print("current TCP (base):", " ".join("%9.3f" % v for v in p))
print("current TCP fanuc :", " ".join("%9.3f" % v for v in r))
