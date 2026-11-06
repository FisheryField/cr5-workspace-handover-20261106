# -*- coding: utf-8 -*-
"""E10->E11 换向分支枚举取证（只读）：
E9  (0,-775,300, 90,0,0)
E10 (0,-750,300, 90,0,0)   P6前退让
E11 (0,-750,300,180,0,0)   P6退让位换向  <- 两次失败点
E12 (0,-762,300,180,0,0)   P6 返回工作位
问题：是否存在 (q10分支, q11分支) 使 MoveJ_Test 通过？
"""
import sys, io, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
assert robot.Valid()

def branches(pose):
    lower, upper, _ = robot.JointLimits()
    lower, upper = lower.list(), upper.list()
    out = []
    for sol in robot.SolveIK_All(pose):
        q = [((float(v) + 180.0) % 360.0) - 180.0 for v in sol[:6]]
        for t6 in (0, -1, 1):
            cand = q[:]
            cand[5] += 360.0 * t6
            if all(lower[j] <= cand[j] <= upper[j] for j in range(6)):
                if not any(max(abs(a-b) for a, b in zip(cand, o)) < 1e-6 for o in out):
                    out.append(cand)
    return out

E10 = Fanuc_2_Pose([0., -750., 300., 90., 0., 0.])
E11 = Fanuc_2_Pose([0., -750., 300., 180., 0., 0.])
saved = robot.Joints().list()[:6]
try:
    b10, b11 = branches(E10), branches(E11)
    print(f'E10 分支数={len(b10)}  E11 分支数={len(b11)}')
    for k, q in enumerate(b10): print(f'  E10[{k}] =', [round(v,1) for v in q])
    for k, q in enumerate(b11): print(f'  E11[{k}] =', [round(v,1) for v in q])

    q0 = b10[0]
    st = robot.MoveL_Test(q0, E11)
    print(f'MoveL_Test(任意E10分支 -> E11位姿) = {st}  （位姿对位姿插值，与分支无关）')

    ok = []
    for i, qa in enumerate(b10):
        for j, qb in enumerate(b11):
            st = robot.MoveJ_Test(qa, qb)
            if st == 0:
                ok.append((i, j, sum((a-b)**2 for a, b in zip(qa, qb))))
            else:
                pairs = RDK.CollisionPairs()
                print(f'E10[{i}] -> E11[{j}]: FAIL({st}) ' + '; '.join(f'{a.Name()}[{ia}]-{b.Name()}[{ib}]' for a,b,ia,ib in pairs))
    if ok:
        ok.sort(key=lambda t: t[2])
        print('可通行组合（按关节距离升序）:')
        for i, j, d in ok: print(f'  E10[{i}] -> E11[{j}]  关节距离²={d:.0f}')
    else:
        print('!! 所有分支组合 MoveJ 均碰撞：该换向步在此工具模型下几何不可行')
finally:
    robot.setJoints(saved)
print('done')
