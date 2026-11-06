# -*- coding: utf-8 -*-
"""把模型摆回 (28.171,-684.989,382.89,-88.93,-59.66,-90.94)。"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
RDK.setRunMode(robolink.RUNMODE_SIMULATE)
q = [58.502, 101.149, -45.185, -54.931, 31.488, -60.548]
robot.setJoints(q)
print('模型已摆回：TCP=(28.171, -684.989, 382.89, -88.93, -59.66, -90.94)')
print('关节 =', ['%.3f' % v for v in q])
print('碰撞检查 =', '碰撞!' if robot.MoveJ_Test(q, q, minstep_deg=1) != 0 else '无碰撞')
OUT = r'D:\mydata\glm-workplace\tools\contact_pose_demo.png'
if os.path.exists(OUT):
    os.remove(OUT)
try:
    RDK.Cam2D_Snapshot(OUT, None)
except Exception:
    RDK.Cam2D_Snapshot(OUT, 0)
print('DONE（SIMULATE）')
