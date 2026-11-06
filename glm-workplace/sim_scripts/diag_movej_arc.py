# -*- coding: utf-8 -*-
"""只读诊断：沿 15:16 那次实跑的 P1→P2→P3 MoveJ 关节弧采样，
看自碰/外碰在哪一段、J4 折叠到多少。场景=Δ+203（圆柱-713）。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import *
from robodk.robomath import *

P1 = [16.379607289924365, -2.702166998945586, -71.53606925601697, -15.761763745037456, 90.0, -73.62039271007563]
P2 = [67.69465952140584, 77.87287831684995, -89.79811557900767, -168.07476273784232, 67.69465952140584, -180.0]
P3 = [-53.43454499405151, -0.1551210872018487, -87.91835620333345, -91.92652270946469, -53.43454499405149, -180.0]

RDK = Robolink()
RDK.setRunMode(RUNMODE_SIMULATE)
robot = RDK.Item('', ITEM_TYPE_ROBOT)
cyl = RDK.Item('磨砂圆柱_R150_H50', ITEM_TYPE_OBJECT)
baffle = RDK.Item('挡板_半封闭3面', ITEM_TYPE_OBJECT)
table = RDK.Item('安装台_650x650x80mm', ITEM_TYPE_OBJECT)
ground = RDK.Item('地面_禁止穿越', ITEM_TYPE_OBJECT)
handle = RDK.Item('门把手_bs1')

for obst in (cyl, baffle, table, ground):
    for link in range(1, 7):
        RDK.setCollisionActivePair(COLLISION_ON, robot, obst, link, 0)
    if handle.Valid():
        RDK.setCollisionActivePair(COLLISION_ON, handle, obst)
RDK.setCollisionActivePair(COLLISION_OFF, robot, table, 0, 0)
for i in range(1, 7):
    for j in range(i + 2, 7):
        RDK.setCollisionActivePair(COLLISION_ON, robot, robot, i, j)
if handle.Valid():
    for link in range(1, 5):
        RDK.setCollisionActivePair(COLLISION_ON, handle, robot, link, 0)
RDK.setCollisionActive(COLLISION_ON)

def sample(a, b, label, n=40):
    print('--- %s ---' % label)
    first = None
    for k in range(n + 1):
        t = k / n
        q = [a[i] + (b[i] - a[i]) * t for i in range(6)]
        robot.setJoints(q)
        col = RDK.Collisions() or 0
        if col and first is None:
            names = ','.join(sorted({i.Name() for i in RDK.CollisionItems()}))
            first = (t, q[:], names)
            print('  首次命中 t=%.2f J4=%.1f 对=%s' % (t, q[3], names))
    if first is None:
        print('  全弧无碰撞（max|J4| 扫过范围 %.1f→%.1f）' % (
            max(abs(a[3]), abs(b[3])), max(abs(a[3]), abs(b[3]))))
    else:
        print('  J4 轨迹：起点 %.1f → 折叠峰值附近采样命中 t=%.2f' % (a[3], first[0]))

sample(P1, P2, 'P1→P2')
sample(P2, P3, 'P2→P3')
robot.setJoints(P2)
print('P2 位形单点：J4=%.1f 碰撞=%s' % (P2[3], RDK.Collisions() or 0))
robot.setJoints([0.0] * 6)
print('DONE（臂回零；场景未动）')
