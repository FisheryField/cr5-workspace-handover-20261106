# -*- coding: utf-8 -*-
"""只读：打印障碍物/机器人的父链与原始位姿，弄清 Pose() 的参考系。"""
from robodk.robolink import *
from robodk.robomath import *

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)

def chain(item):
    names = []
    p = item
    while p.Valid():
        names.append('%s(type=%s)' % (p.Name(), p.Type()))
        p = p.Parent()
    return ' <- '.join(names)

print('robot chain:', chain(robot))
print('robot.Pose() =')
for row in robot.Pose().rows:
    print('   ', ['%9.3f' % v for v in row])
print('robot.PoseWrtStation?? not avail; robot.Joints() =', robot.Joints().list())

for name in ('安装台_650x650x80mm', '地面_禁止穿越', '磨砂圆柱_R150_H50', '挡板_半封闭3面'):
    it = RDK.Item(name, ITEM_TYPE_OBJECT)
    if not it.Valid():
        print(name, 'MISSING'); continue
    print('%s chain: %s' % (name, chain(it)))
    print('   Pose() =')
    for row in it.Pose().rows:
        print('      ', ['%9.3f' % v for v in row])
    G = it.GeometryPose()
    print('   GeometryPose() =')
    for row in G.rows:
        print('      ', ['%9.3f' % v for v in row])

# 参考：法兰 FK（基座系）当前值
print('robot flange FK (base) xyz =', ['%9.3f' % v for v in [robot.SolveFK(robot.Joints())[0,3], robot.SolveFK(robot.Joints())[1,3], robot.SolveFK(robot.Joints())[2,3]]])
