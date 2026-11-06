# -*- coding: utf-8 -*-
"""圆柱 y+45（−886→−841）→ 当前模型位姿碰撞检查 → 轨迹16 整段预检。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose, Pose_2_Fanuc

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
it = RDK.Item('磨砂圆柱_R150_H50')
p = Pose_2_Fanuc(it.Pose())
print('圆柱 y: %.1f -> %.1f' % (p[1], p[1] + 45.0))
it.setPose(Fanuc_2_Pose([p[0], p[1] + 45.0, p[2], p[3], p[4], p[5]]))
p2 = Pose_2_Fanuc(it.Pose())
print('圆柱现在 = (%.1f, %.1f, %.1f)' % (p2[0], p2[1], p2[2]))

q = [float(v) for v in robot.Joints().list()[:6]]
print('当前模型关节 =', ['%.2f' % v for v in q])
RDK.setRunMode(robolink.RUNMODE_SIMULATE)
hit = robot.MoveJ_Test(q, q, minstep_deg=1) != 0
print('当前位姿碰撞 =', '是' if hit else '否')
RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
print('DONE（移动已完成；预检另行运行）')
