# -*- coding: utf-8 -*-
"""只读诊断：两个位形下枚举碰撞对（含连杆号）。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import *
from robodk.robomath import *

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
RDK.setCollisionActive(COLLISION_ON)

def dump(label, joints):
    robot.setJoints(joints)
    lst = RDK.CollisionPairs()
    print('%s 关节=%s 碰撞对数=%d' % (label, ['%.1f' % v for v in joints], len(lst) if lst else 0))
    for pair in (lst or []):
        print('   ', pair)

dump('家位(全零)', [0.0]*6)
dump('接触位形', [75.8, 106.1, -81.8, -24.3, -75.8, 0.0])
dump('转运位(500,0,470) 试解', [0.0]*6)   # 先占位；下面用 IK 摆
pose = Fanuc_2_Pose((500, 0, 470, 180, 0, 0))
q = robot.SolveIK(pose * invH(robot.PoseTool()), [0.0]*6)
if q is not None:
    dump('转运位(IK)', q.list()[:6])
else:
    print('转运位 IK 失败')
robot.setJoints([0.0]*6)
print('DONE（臂已回零）')
