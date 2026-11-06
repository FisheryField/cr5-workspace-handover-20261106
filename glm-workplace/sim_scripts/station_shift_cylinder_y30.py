# -*- coding: utf-8 -*-
"""圆柱 +y 平移 30mm：磨砂圆柱_R180_H40 位姿 y -956 → -926（与连续轨迹工作点匹配）。
只改位姿（几何/名字/父级不动），幂等（重复执行结果相同），不保存工作站。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import Robolink, ITEM_TYPE_OBJECT
from robodk.robomath import Pose_2_Fanuc, Fanuc_2_Pose

NAME = '磨砂圆柱_R180_H40'
NEW_Y = -926.0   # 原 -956 + 30

RDK = Robolink()
it = RDK.Item(NAME, ITEM_TYPE_OBJECT)
assert it.Valid(), '未找到 ' + NAME
f = Pose_2_Fanuc(it.Pose())
print('旧位姿 Fanuc =', ['%.3f' % v for v in f])
f[1] = NEW_Y
it.setPose(Fanuc_2_Pose(f))
g = Pose_2_Fanuc(it.Pose())
print('新位姿 Fanuc =', ['%.3f' % v for v in g])
ok = (abs(g[1] - NEW_Y) < 1e-9 and abs(g[0] - f[0]) < 1e-9 and abs(g[2] - f[2]) < 1e-9
      and all(abs(g[k] - f[k]) < 1e-9 for k in (3, 4, 5)))
print('回读一致（含旋转不变） =', ok)
print('DONE（未保存工作站）')
