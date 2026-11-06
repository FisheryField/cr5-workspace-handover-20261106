# -*- coding: utf-8 -*-
"""只读站几何改动：磨砂圆柱_R150_H50 统一 +Y 挪 35mm（−922 → −887）。
打印前后 pose；不保存工作站。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose, Pose_2_Fanuc

DY = -35.0
RDK = robolink.Robolink()
it = RDK.Item('磨砂圆柱_R150_H50')
assert it.Valid(), '滚轮不存在'
p = Pose_2_Fanuc(it.Pose())
print('BEFORE pose = (%.2f, %.2f, %.2f, %.1f, %.1f, %.1f)' % tuple(p))
it.setPose(Fanuc_2_Pose([p[0], p[1] + DY, p[2], p[3], p[4], p[5]]))
p2 = Pose_2_Fanuc(it.Pose())
print('AFTER  pose = (%.2f, %.2f, %.2f, %.1f, %.1f, %.1f)' % tuple(p2))
assert abs(p2[1] - (p[1] + DY)) < 1e-6
print('DONE：滚轮已 +%.0fmm（新中心 y=%.1f，赤道面 y=%.1f）' % (DY, p2[1], p2[1] + 150))
