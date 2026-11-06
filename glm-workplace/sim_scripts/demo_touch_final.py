# -*- coding: utf-8 -*-
"""把模型摆到实测贴面演示位 TCP=(0,-707.2,380,0,-90,180) 并截图。"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose, invH

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
RDK.setRunMode(robolink.RUNMODE_SIMULATE)
T = Fanuc_2_Pose([0.0, -707.2, 380.0, 0.0, -90.0, 180.0])
fl = robot.PoseFrame() * T * invH(robot.PoseTool())
s = robot.SolveIK_All(fl).tolist()
if s and isinstance(s[0], (int, float)):
    s = [s]
assert s, '无解'
q = [float(v) for v in s[0][:6]]
print('关节 =', ['%.2f' % v for v in q])
print('碰撞检查 =', '碰撞!' if robot.MoveJ_Test(q, q, minstep_deg=1) != 0 else '无碰撞')
robot.setJoints(q)
OUT = r'D:\mydata\glm-workplace\tools\contact_pose_demo.png'
if os.path.exists(OUT):
    os.remove(OUT)
try:
    RDK.Cam2D_Snapshot(OUT, None)
except Exception:
    RDK.Cam2D_Snapshot(OUT, 0)
print('截图 =', OUT if os.path.exists(OUT) else '失败')
print('DONE')
