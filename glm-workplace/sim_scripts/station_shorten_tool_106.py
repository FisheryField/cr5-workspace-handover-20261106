# -*- coding: utf-8 -*-
"""末端工具坐标缩短：相对法兰 z 159.629 → 106（减小把手与法兰间连接件 53.629mm）。
同步：门把手_bs1 的 GeometryPose z 159.500 → 105.871（保持 TCP 与网格锚点的既有 −0.129 偏置，
姿态 (−90,0,0) 与 xy 不变），使运动学与碰撞模型一致。
幂等；不保存工作站。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import Robolink
from robodk.robomath import Fanuc_2_Pose, Pose_2_Fanuc

OLD_T, NEW_T = 159.629, 106.0
DELTA = NEW_T - OLD_T            # -53.629
OLD_H, NEW_H = 159.500, 159.500 + DELTA   # 105.871

RDK = Robolink()
robot = RDK.Item('', 0) if False else None
from robodk.robolink import ITEM_TYPE_ROBOT
robot = RDK.Item('', ITEM_TYPE_ROBOT)
assert robot.Valid(), '未找到机器人'

# 1) 工具坐标
robot.setPoseTool(Fanuc_2_Pose([0.0, 0.0, NEW_T, 0.0, 0.0, 0.0]))
t = Pose_2_Fanuc(robot.PoseTool())
print('工具 Fanuc =', ['%.3f' % v for v in t])
assert abs(t[2] - NEW_T) < 1e-9 and all(abs(t[k]) < 1e-9 for k in (0, 1, 3, 4, 5))

# 2) 把手几何偏移同步
h = RDK.Item('门把手_bs1')
assert h.Valid(), '未找到 门把手_bs1'
g = Pose_2_Fanuc(h.GeometryPose())
print('把手 GeometryPose 旧 =', ['%.3f' % v for v in g])
h.setGeometryPose(Fanuc_2_Pose([g[0], g[1], NEW_H, g[3], g[4], g[5]]))
g2 = Pose_2_Fanuc(h.GeometryPose())
print('把手 GeometryPose 新 =', ['%.3f' % v for v in g2])
assert abs(g2[2] - NEW_H) < 1e-6

print('DONE：TCP z=%.3f，把手网格 z=%.3f（同步 Δ=%.3f mm）；未保存工作站' % (t[2], g2[2], DELTA))
