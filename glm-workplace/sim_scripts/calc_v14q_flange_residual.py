# -*- coding: utf-8 -*-
"""calc_v14q_flange_residual.py — v14q 设计输入：昨天 v14p 首航 P5 停点的法兰位姿级残差
数据源：real_gui_log_p2p.txt L1127-1130（2026-10-12 18:50:42-43）
  命令目标关节 P5 = [-63.41392174214575, -23.452600702069375, -86.6540412190377, -69.8933580788929, -63.41392174214576, -180.0]
  停点实测关节   = [-62.92547349811615, -22.86712072046328, -87.6013220692609, -69.22431865818909, -63.4373989887814, -180.34503500191286]
  （关节级最大偏差 0.95° 触发 v14p 护栏拦停）
目的：算 FK(实测) vs FK(目标) 的法兰位置差(mm) 与姿态差(°) —— v14p 补偿 MOVL 的真实语义是
     把法兰送到 FK(joints) 位姿，所以验收判据也应是法兰级，不是关节级。
只读工作站，不改任何东西；不连实机。
"""
import sys, math
import robodk as rdk  # eye, invH, norm, pose_angle

from robolink import Robolink

RDK = Robolink()
robot = RDK.Item('Dobot CR5', 2)  # ITEM_TYPE_ROBOT=2
if not robot.Valid():
    robots = [it.Name() for it in RDK.ItemList(2) if it.Valid()]
    print('!! 未找到 Dobot CR5，站内机器人：', robots)
    sys.exit(1)

print('机器人:', robot.Name(), '| 站内工具数:', len([t for t in robot.Childs() if t.Type() == 3]))

TARGET = [-63.41392174214575, -23.452600702069375, -86.6540412190377,
          -69.8933580788929, -63.41392174214576, -180.0]
STOP = [-62.92547349811615, -22.86712072046328, -87.6013220692609,
        -69.22431865818909, -63.4373989887814, -180.34503500191286]

saved_tool = robot.PoseTool()
try:
    robot.setPoseTool(rdk.eye(4))  # 法兰系：与 v14p 发送时同态
    f_t = robot.SolveFK(TARGET)
    f_s = robot.SolveFK(STOP)
finally:
    robot.setPoseTool(saved_tool)

delta = f_s * rdk.invH(f_t)
d_pos = rdk.norm(delta.Pos())
d_ang = math.degrees(rdk.pose_angle(delta))

jmax = max(abs(s - t) for s, t in zip(STOP, TARGET))

print('--- 关节级（v14p 现行判据，0.5° 容差）---')
print('最大关节偏差: %.3f°  -> %s' % (jmax, 'FAIL(>0.5)' if jmax > 0.5 else 'PASS'))
print('--- 法兰位姿级（v14q 候选判据）---')
print('法兰位置差: %.3f mm' % d_pos)
print('法兰姿态差: %.3f°' % d_ang)
print('--- 判读 ---')
print('若 d_pos<=2.0 且 d_ang<=0.5 -> v14q 判据下昨日停点应判 PASS（护栏阈值问题，非落点问题）')
print('法兰位姿矩阵 delta 平移分量: [%.3f, %.3f, %.3f]' % (delta[0,3], delta[1,3], delta[2,3]))
