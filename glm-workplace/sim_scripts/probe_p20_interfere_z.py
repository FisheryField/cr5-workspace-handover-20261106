# -*- coding: utf-8 -*-
"""只读：P20 姿态 (40,-624,z,90,0,90) 在各 z 下的干净分支数（避开 J4×J5 自干涉组合区）。
同时打印该 z 下统一下视簇代表点 P10 (100,y,z,180) 的最远可解 y（供 Δ 决策）。
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT
from robodk.robomath import Fanuc_2_Pose

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
frame = robot.PoseFrame()
tool = Fanuc_2_Pose([0.0, 0.0, 182.0, 0.0, 0.0, 0.0])
J4MAX, J5MIN = 100.0, 165.0

def all_ik(x, y, z, rx, ry, rz):
    q = robot.SolveIK_All(Fanuc_2_Pose([float(x), float(y), float(z), float(rx), float(ry), float(rz)]),
                          tool=tool, reference=frame)
    try:
        rows = q.rows   # 6 行 × N 列
    except Exception:
        return []
    if not rows or len(rows) < 6:
        return []
    n = len(rows[0])
    sols = []
    for c in range(n):
        sols.append([rows[r][c] for r in range(6)])
    return sols

def interfere(q):
    return abs(q[3]) > J4MAX and abs(q[4]) > J5MIN

print('z     P20解数  干涉解  干净解')
for z in (570.0, 500.0, 470.0, 450.0, 430.0, 410.0, 395.0, 380.0, 365.0):
    sols = all_ik(40, -624, z, 90, 0, 90)
    bad = sum(1 for s in sols if interfere(s))
    print('%-6.0f %-8d %-8d %d' % (z, len(sols), bad, len(sols) - bad))

print()
print('P10 (100, y, z, 180,0,0) 最远可解 y（y 从 −600 朝负步 −5）:')
for z in (470.0, 425.0, 410.0, 395.0, 380.0):
    y = -600.0
    sols = all_ik(100, y, z, 180, 0, 0)
    if not sols:
        # 从 −550 找可解再往远
        y = -550.0
        while y > -750.0 and not all_ik(100, y, z, 180, 0, 0):
            y -= 5.0
    while y > -800.0 and all_ik(100, y - 5.0, z, 180, 0, 0):
        y -= 5.0
    print('z=%-6.0f 最远 y=%.0f' % (z, y))
print('DONE')
