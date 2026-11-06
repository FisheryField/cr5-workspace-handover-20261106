# -*- coding: utf-8 -*-
"""临时把 PoseTool 置 (0,0,139)（what-if 测试用）。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose
RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
robot.setPoseTool(Fanuc_2_Pose([0.0, 0.0, 182.0, 0.0, 0.0, 0.0]))
print('PoseTool =', robot.PoseTool().Pos())
print('DONE')
