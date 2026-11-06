# -*- coding: utf-8 -*-
"""幂等确认一体单元在 Δ=+76（圆柱 y=-840、挡板 y=76），并打印回读。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import *

RDK = Robolink()
cyl = RDK.Item('磨砂圆柱_R150_H50', ITEM_TYPE_OBJECT)
baffle = RDK.Item('挡板_半封闭3面', ITEM_TYPE_OBJECT)
for it, ty in ((cyl, -840.0), (baffle, 76.0)):
    P = it.Pose()
    print('%s 当前 t=(%.1f, %.1f, %.1f)' % (it.Name(), P[0, 3], P[1, 3], P[2, 3]))
    if abs(P[1, 3] - ty) > 1e-9:
        P[1, 3] = ty
        it.setPose(P)
        print('  → 已纠正 y=%.1f' % ty)
print('DONE（未保存工作站）')
