# -*- coding: utf-8 -*-
"""只读：查 SolveIK 原始返回与签名差异。"""
from robodk.robolink import *
from robodk.robomath import *

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
if not robot.Valid():
    raise SystemExit('ERROR: 未找到机器人')

T = Fanuc_2_Pose([500.0, 0.0, 300.0, 180.0, 0.0, 0.0])

r1 = robot.SolveIK(T)
print('SolveIK(T) ->', type(r1), repr(r1))

r2 = robot.SolveIK(T, tool=robot.PoseTool(), reference=robot.PoseFrame())
print('SolveIK(T,tool,reference) ->', type(r2), repr(r2))

r3 = robot.SolveIK(T, robot.PoseTool(), robot.PoseFrame())
print('SolveIK positional ->', type(r3), repr(r3))

# 宏 L1351 同款：FK→TCP 正向，确认正向链路活着
try:
    q0 = robot.SimulateJoints()
    print('SimulateJoints ->', repr(q0))
    fk = robot.SolveFK(q0)
    print('SolveFK(q0) ->', ['%.2f' % v for v in Pose_2_Fanuc(fk)])
except Exception as exc:
    print('FK test EXC:', type(exc).__name__, exc)

print('DONE')
