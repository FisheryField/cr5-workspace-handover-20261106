# -*- coding: utf-8 -*-
"""只读：读当前模型冻结姿态与碰撞状态。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import socket
socket.setdefaulttimeout(12)
from robodk import robolink

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
print('模型当前关节 =', ['%.4f' % v for v in robot.Joints().list()[:6]])
print('PoseTool =', robot.PoseTool().Pos())

for name, fn in [
    ('RDK.Collisions()', lambda: RDK.Collisions()),
    ('robot.Collisions()', lambda: robot.Collisions()),
]:
    try:
        r = fn()
        print('%s -> %s' % (name, r))
    except Exception as e:
        print('%s -> EXC %s' % (name, e))

for nm in ('门把手_bs1', '磨砂圆柱_R150_H50', '安装台_650x650x80mm', '地面_禁止穿越', '挡板_半封闭3面'):
    it = RDK.Item(nm)
    if not it.Valid():
        print(nm, '不存在')
        continue
    try:
        c = it.Colliding()
        print('%s.Colliding() -> %s' % (nm, c))
    except Exception as e:
        print('%s.Colliding() EXC %s' % (nm, e))
    try:
        lst = it.CollidingItems() if hasattr(it, 'CollidingItems') else None
        if lst is not None:
            print('%s.CollidingItems -> %s' % (nm, [x.Name() for x in lst]))
    except Exception as e:
        print('%s.CollidingItems EXC %s' % (nm, e))
print('DONE')
