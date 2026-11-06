# -*- coding: utf-8'
"""诊断：已知可达点 P8(0,-706,380,180,0,0) 的 IK 是否也失败——判定环境降级 vs 真不可达。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import socket
socket.setdefaulttimeout(15)
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose, invH

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
print('Version:', RDK.Version())
qj = robot.Joints().list()
print('Joints raw len =', len(qj), '->', [round(float(v), 2) for v in qj[:6]])
print('PoseTool =', robot.PoseTool().Pos())

for name, T in [
    ('P8 已知可达 (0,-706,380,180,0,0)', Fanuc_2_Pose([0.0, -706.0, 380.0, 180.0, 0.0, 0.0])),
    ('P1 零位附近 (500,0,380,180,0,0)', Fanuc_2_Pose([500.0, 0.0, 380.0, 180.0, 0.0, 0.0])),
]:
    fl = robot.PoseFrame() * T * invH(robot.PoseTool())
    try:
        s = robot.SolveIK_All(fl).tolist()
        if s and isinstance(s[0], (int, float)):
            s = [s]
        print('%s -> %d 解' % (name, len(s)))
    except Exception as e:
        print('%s -> EXC %s' % (name, e))
print('DONE')
