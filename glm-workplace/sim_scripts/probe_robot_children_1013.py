# -*- coding: utf-8 -*-
"""probe_robot_children_1013.py — 确认门把手_bs1 挂载与激活状态（只读）"""
from robolink import Robolink
import robodk as rdk

RDK = Robolink()
robot = RDK.Item('Dobot CR5', 2)
print('机器人:', robot.Name())
print('子项:', [c.Name() for c in robot.Childs()])
pt = robot.PoseTool()
print('当前 PoseTool 平移: [%.3f, %.3f, %.3f] mm' % (pt[0, 3], pt[1, 3], pt[2, 3]))
print('当前 PoseFrame 平移: [%.3f, %.3f, %.3f] mm' % (robot.PoseFrame()[0,3], robot.PoseFrame()[1,3], robot.PoseFrame()[2,3]))
print('判断: 工具平移模长 %.3f mm（期望 ~159.63 = 门把手_bs1 激活；~0 = 法兰裸态）' % rdk.norm(pt.Pos()))
