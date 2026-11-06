# -*- coding: utf-8 -*-
"""场景永久改动：磨砂圆柱+挡板 一起 y-26（−860→−886 / 56→30）。打印前后值。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose, Pose_2_Fanuc

DY = -26.0
RDK = robolink.Robolink()
for name in ('磨砂圆柱_R150_H50', '挡板_半封闭3面'):
    it = RDK.Item(name)
    assert it.Valid(), name
    p = Pose_2_Fanuc(it.Pose())
    print('%s BEFORE y=%.1f' % (name, p[1]))
    it.setPose(Fanuc_2_Pose([p[0], p[1] + DY, p[2], p[3], p[4], p[5]]))
    p2 = Pose_2_Fanuc(it.Pose())
    print('%s AFTER  y=%.1f  (Δ=%.1f)' % (name, p2[1], p2[1] - p[1]))
print('DONE：场景已永久 −26（不保存工作站；实物须同步）')
