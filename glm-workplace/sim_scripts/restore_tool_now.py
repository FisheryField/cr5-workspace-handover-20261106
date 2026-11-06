# -*- coding: utf-8 -*-
"""现场恢复：PoseTool=0 → 恢复规范 (0,0,182)；门把手隐藏 → 恢复显示。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)

t = robot.PoseTool().Pos()
print('当前 PoseTool =', ['%.3f' % v for v in t])
if abs(t[0]) < 1e-9 and abs(t[1]) < 1e-9 and abs(t[2]) < 1e-9:
    robot.setPoseTool(Fanuc_2_Pose([0.0, 0.0, 182.0, 0.0, 0.0, 0.0]))
    print('已恢复 PoseTool = [0, 0, 182]')
else:
    print('PoseTool 非零，不干预')

h = RDK.Item('门把手_bs1')
if h.Valid() and not h.Visible():
    h.setVisible(True)
    print('门把手处于隐藏态——已恢复显示')
else:
    print('门把手显示正常')
print('DONE')
