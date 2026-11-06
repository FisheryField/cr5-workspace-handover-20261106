# -*- coding: utf-8 -*-
"""撤回 v14w8 的 +z50：圆柱（现名 磨砂圆柱_R150_H50）位姿 z 350 → 300。
只改位姿，幂等，不保存工作站。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import Robolink, ITEM_TYPE_OBJECT
from robodk.robomath import Pose_2_Fanuc, Fanuc_2_Pose

NAME = '磨砂圆柱_R150_H50'
NEW_Z = 300.0   # 撤回抬高：350 - 50

RDK = Robolink()
it = RDK.Item(NAME, ITEM_TYPE_OBJECT)
assert it.Valid(), '未找到 ' + NAME
f = Pose_2_Fanuc(it.Pose())
print('旧位姿 Fanuc =', ['%.3f' % v for v in f])
f[2] = NEW_Z
it.setPose(Fanuc_2_Pose(f))
g = Pose_2_Fanuc(it.Pose())
print('新位姿 Fanuc =', ['%.3f' % v for v in g])
ok = (abs(g[2] - NEW_Z) < 1e-9 and all(abs(g[k] - f[k]) < 1e-9 for k in (0, 1, 3, 4, 5)))
print('回读一致（含 xy/旋转不变） =', ok)
print('DONE（未保存工作站）')
