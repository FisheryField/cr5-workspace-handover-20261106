# -*- coding: utf-8 -*-
"""只读诊断：SolveIK 在不同 tool 下的语义与可达性（2026-10-20）。不发运动、不保存。"""
from robodk.robolink import *
from robodk.robomath import *
import math

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
if not robot.Valid():
    raise SystemExit('ERROR: 未找到机器人')

frame = robot.PoseFrame()
print('PoseFrame Pos:', ['%.3f' % v for v in Pose_2_Fanuc(frame)])
print('当前 PoseTool:', ['%.3f' % v for v in Pose_2_Fanuc(robot.PoseTool())])

tests = [
    ('[0,-775,300,90,0,0]', [0.0, -775.0, 300.0, 90.0, 0.0, 0.0]),
    ('[500,0,300,180,0,0]', [500.0, 0.0, 300.0, 180.0, 0.0, 0.0]),
    ('[0,-615,300,90,0,0]', [0.0, -615.0, 300.0, 90.0, 0.0, 0.0]),
]
tools = [
    ('tool=0(eye)', Fanuc_2_Pose([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])),
    ('tool=100', Fanuc_2_Pose([0.0, 0.0, 100.0, 0.0, 0.0, 0.0])),
    ('tool=182', Fanuc_2_Pose([0.0, 0.0, 182.0, 0.0, 0.0, 0.0])),
]

for name, vals in tests:
    T = Fanuc_2_Pose(vals)
    for tname, tp in tools:
        try:
            q = robot.SolveIK(T, tool=tp, reference=frame)
            if q is None or len(q) != 6:
                print('%s | %s -> q=None/len!=6' % (name, tname))
                continue
            tcp = invH(frame) * robot.SolveFK(q) * tp
            flg = invH(frame) * robot.SolveFK(q)
            d_tcp = norm((invH(T) * tcp).Pos())
            d_flg = norm((invH(T) * flg).Pos())
            print('%s | %s -> q=[%s]  d(TCP,T)=%.2f  d(Flange,T)=%.2f' % (
                name, tname, ','.join('%.1f' % v for v in q), d_tcp, d_flg))
        except Exception as exc:
            print('%s | %s -> EXC %s: %s' % (name, tname, type(exc).__name__, exc))

print('DONE（只读）')
