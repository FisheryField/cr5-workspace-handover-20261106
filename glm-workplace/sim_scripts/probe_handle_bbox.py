# -*- coding: utf-8 -*-
# 只读：把手 STL 包围盒 + 站内项位姿
import sys, io, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk.robolink import Robolink, ITEM_TYPE_OBJECT, ITEM_TYPE_ROBOT
from robodk.robomath import Pose_2_Fanuc

def stl_bbox(path):
    d = open(path, 'rb').read()
    n = struct.unpack_from('<I', d, 80)[0]
    xs = ys = zs = []
    xs, ys, zs = [], [], []
    off = 84
    for i in range(n):
        base = off + i * 50
        for k in range(3):
            vi = base + 12 + k * 12
            x, y, z = struct.unpack_from('<3f', d, vi)
            xs.append(x); ys.append(y); zs.append(z)
    return n, (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))

for p in [r'D:\mydata\glm-workplace\tools\handle_shortened_99.stl',
          r'D:\mydata\glm-workplace\tools\handle_export_test.stl',
          r'D:\mydata\glm-workplace\tools\handle_bs1.stl']:
    n, xb, yb, zb = stl_bbox(p)
    print('%s  三角=%d' % (p.split('\\')[-1], n))
    print('   X[%.3f, %.3f]  Y[%.3f, %.3f]  Z[%.3f, %.3f]' % (xb[0], xb[1], yb[0], yb[1], zb[0], zb[1]))

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
print('PoseTool =', ['%.3f' % v for v in Pose_2_Fanuc(robot.PoseTool())])
for name in ['门把手_bs1']:
    it = RDK.Item(name)
    if it.Valid():
        print(name, 'parent=', it.Parent().Name())
        print('  pose =', ['%.3f' % v for v in Pose_2_Fanuc(it.Pose())])
        print('  geo  =', ['%.3f' % v for v in Pose_2_Fanuc(it.GeometryPose())])
        print('  type =', it.Type())
