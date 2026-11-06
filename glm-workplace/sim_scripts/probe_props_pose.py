# -*- coding: utf-8 -*-
# 只读：读站内 圆柱/挡板 当前位姿
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk.robolink import Robolink
from robodk.robomath import Pose_2_Fanuc

RDK = Robolink()
for name in ['磨砂圆柱_R150_H50', '挡板_半封闭3面']:
    it = RDK.Item(name)
    if not it.Valid():
        print(name, 'NOT FOUND'); continue
    p = Pose_2_Fanuc(it.Pose())
    g = Pose_2_Fanuc(it.GeometryPose())
    print('%-16s parent=%-16s pose=(%.1f,%.1f,%.1f, %.1f,%.1f,%.1f)  geo=(%.1f,%.1f,%.1f, %.1f,%.1f,%.1f)'
          % (name, it.Parent().Name(), p[0], p[1], p[2], p[3], p[4], p[5],
             g[0], g[1], g[2], g[3], g[4], g[5]))
