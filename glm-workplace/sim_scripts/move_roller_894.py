# -*- coding: utf-8 -*-
"""方案A：滚轮中心 y=-894（P2 y=-687，抓手尖在 TCP−56=-743，面=-744 ⇒ 1mm）→ 预检。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose, Pose_2_Fanuc

RDK = robolink.Robolink()
cyl = RDK.Item('磨砂圆柱_R150_H50')
p = Pose_2_Fanuc(cyl.Pose())
print('滚轮 y: %.1f -> -894.0' % p[1])
cyl.setPose(Fanuc_2_Pose([p[0], -894.0, p[2], p[3], p[4], p[5]]))
p2 = Pose_2_Fanuc(cyl.Pose())
print('滚轮现在 = (%.1f, %.1f, %.1f)  赤道面 y=%.1f' % (p2[0], p2[1], p2[2], p2[1] + 150))
print('P2 尖端(182) y=-743.0 → 距面 %.1fmm' % ((p2[1] + 150) - (-743.0)))
print('DONE')
