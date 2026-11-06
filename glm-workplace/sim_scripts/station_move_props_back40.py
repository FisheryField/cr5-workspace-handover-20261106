# -*- coding: utf-8 -*-
# 圆柱+挡板 再后移 40mm（面表 −782→−822），为工作点 W 的工具-朝上变体让出抓手间隙。不保存工作站。
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk.robolink import Robolink
from robodk.robomath import Pose_2_Fanuc, Fanuc_2_Pose

RDK = Robolink()
DY = -40.0
for name in ['磨砂圆柱_R150_H50', '挡板_半封闭3面']:
    it = RDK.Item(name)
    p = Pose_2_Fanuc(it.Pose())
    it.setPose(Fanuc_2_Pose([p[0], p[1] + DY, p[2], p[3], p[4], p[5]]))
    p2 = Pose_2_Fanuc(it.Pose())
    print('%-14s pose.y %.1f → %.1f' % (name, p[1], p2[1]))
print('DONE（未保存）')
