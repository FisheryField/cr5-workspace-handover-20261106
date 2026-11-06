# -*- coding: utf-8 -*-
"""宏同款路径复现：用健康链关节（Δ=+76 落位结果）逐段 MoveJ_Test/MoveL_Test，
碰撞对与宏预检一致（links1-6×四障碍、把手×四障碍、link0×安装台 OFF、关自碰残留）。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import *
from robodk.robomath import *

QS = [
    [16.4, -2.7, -71.5, -15.8, 90.0, -73.6],
    [73.6, 16.7, 68.5, 94.8, 73.6, -180.0],
    [85.2, 18.2, 66.5, 95.3, 85.2, -180.0],
    [85.2, 18.2, 66.5, 95.3, 85.2, 0.0],
    [73.6, 16.7, 68.5, 94.8, 73.6, 0.0],
    [78.1, 34.6, 26.6, 28.8, -90.0, 168.1],
    [78.1, 34.6, 26.6, 28.8, -90.0, 168.1],
    [86.6, 36.7, 22.8, 30.5, -90.0, 176.6],
    [86.6, 36.7, 22.8, 30.5, -90.0, 356.6],
    [78.1, 34.6, 26.6, 28.8, -90.0, 348.1],
    [68.6, -7.1, 63.0, 34.0, -90.0, 338.6],
    [-98.5, -96.7, 98.7, -2.0, -171.5, 180.0],
    [-92.9, -96.5, 101.5, -4.9, -177.1, 180.0],
    [64.9, 82.3, -36.6, -45.6, 25.1, 180.0],
    [64.9, 95.9, -50.7, -45.3, 25.1, 180.0],
    [64.7, 95.2, -48.6, -46.6, 25.3, 180.0],
    [64.7, 95.2, -48.6, -46.6, 25.3, 180.0],
    [62.9, 88.3, -53.9, -34.4, 27.1, 180.0],
    [-166.4, -17.7, -53.2, -19.1, 90.0, 193.6],
]

RDK = Robolink()
RDK.setRunMode(RUNMODE_SIMULATE)
robot = RDK.Item('', ITEM_TYPE_ROBOT)
cyl = RDK.Item('磨砂圆柱_R150_H50', ITEM_TYPE_OBJECT)
baffle = RDK.Item('挡板_半封闭3面', ITEM_TYPE_OBJECT)
table = RDK.Item('安装台_650x650x80mm', ITEM_TYPE_OBJECT)
ground = RDK.Item('地面_禁止穿越', ITEM_TYPE_OBJECT)
handle = RDK.Item('门把手_bs1')
print('场景：圆柱 y=%.1f 挡板 y=%.1f' % (cyl.Pose()[1, 3], baffle.Pose()[1, 3]))

# 宏同款：先关掉可能残留的自碰对，再开宏的对集
for i in range(1, 7):
    for j in range(i + 1, 7):
        RDK.setCollisionActivePair(COLLISION_OFF, robot, robot, i, j)
if handle.Valid():
    for link in range(1, 7):
        RDK.setCollisionActivePair(COLLISION_OFF, handle, robot, link, 0)
for obst in (cyl, baffle, table, ground):
    for link in range(1, 7):
        RDK.setCollisionActivePair(COLLISION_ON, robot, obst, link, 0)
    if handle.Valid():
        RDK.setCollisionActivePair(COLLISION_ON, handle, obst)
RDK.setCollisionActivePair(COLLISION_OFF, robot, table, 0, 0)
RDK.setCollisionActive(COLLISION_ON)

def pair_detail():
    n = RDK.Collisions() or 0
    if not n:
        return '-'
    return ','.join(sorted({i.Name() for i in RDK.CollisionItems()}))

bad = []
for i in range(len(QS) - 1):
    a, b = QS[i], QS[i + 1]
    st = robot.MoveJ_Test(a, b, minstep_deg=5)
    detail = pair_detail() if st != 0 else '-'
    tag = 'MoveJ OK' if st == 0 else 'MoveJ X(%s) %s' % (st, detail)
    fb = ''
    if st != 0:
        st2 = robot.MoveJ_Test(a, b, minstep_deg=1)
        if st2 == 0:
            fb = '细采样后OK'
        else:
            pose_b = robot.SolveFK(b) * robot.PoseTool()
            stl = robot.MoveL_Test(a, pose_b, minstep_mm=10)
            if stl == 0:
                fb = '→ MoveL可通行'
            else:
                stl2 = robot.MoveL_Test(a, pose_b, minstep_mm=1)
                fb = '→ MoveL也不通(%s) %s' % (stl2, pair_detail())
                bad.append((i, i + 1))
    print('P%02d→P%02d  %-22s %s' % (i + 1, i + 2, tag, fb))

print('=== 双路皆死的段：', bad if bad else '无（弧碰段可由 MoveL 兜底）')
robot.setJoints([0.0] * 6)
print('DONE（臂回零；场景未动）')
