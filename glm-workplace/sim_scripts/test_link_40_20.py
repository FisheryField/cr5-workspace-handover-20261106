# -*- coding: utf-8 -*-
"""测连接：清分支 (40,-694,0°) → 清分支 (20,-700,0°) 的 MoveJ 弧是否可行。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import invH, rotz

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_head', 'exec'), ns)
fanuc_to_pose = ns['fanuc_values_to_pose']
ns['_ensure_canonical_tool']()

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT')
RDK.setRunMode(robolink.RUNMODE_SIMULATE)

def clear_branches(x, y):
    T = fanuc_to_pose(x, y, 380.0, 90.0, 0.0, 90.0)
    fl = robot.PoseFrame() * T * invH(robot.PoseTool())
    s = robot.SolveIK_All(fl).tolist()
    if s and isinstance(s[0], (int, float)):
        s = [s]
    out = []
    for sol in s:
        q = [float(v) for v in sol[:6]]
        if robot.MoveJ_Test(q, q, minstep_deg=1) == 0:
            out.append(q)
    return out

A = clear_branches(40.0, -694.0)   # 过渡点清分支
B = clear_branches(20.0, -700.0)   # P14 清分支
print('(40,-694) 清分支数 =', len(A), ' ; (20,-700) 清分支数 =', len(B))
ok = 0
for qa in A:
    for qb in B:
        if robot.MoveJ_Test(qa, qb, minstep_deg=1) == 0:
            ok += 1
print('过渡→P14 弧组合可行数 =', ok, '/', len(A) * len(B))
RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
print('DONE')
