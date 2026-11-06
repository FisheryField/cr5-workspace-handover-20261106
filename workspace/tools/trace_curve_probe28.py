#!/usr/bin/env python3
"""探针28：验证重建曲线的两个数学环节。
① robot.SolveFK(q, tool).Pos() 是否等于该关节下 tool.PoseAbs().Pos()
② 关节线性插值 + SolveFK 采样出的路径是否平滑合理（MoveJ 即关节线性）
③ AddCurve 收 ~400 点是否正常
"""
from robodk import robomath
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT, ITEM_TYPE_TOOL

RDK = Robolink()
robot = RDK.Item("", ITEM_TYPE_ROBOT)
tool = robot.getLink(ITEM_TYPE_TOOL)
print("tool:", tool.Name() if tool.Valid() else "(invalid)")

q0 = robot.Joints().list()[:6]
tool_pose = tool.PoseTool()
base_pose = robot.PoseAbs()
p_abs = tool.PoseAbs().Pos()
p_fk_flange = robot.SolveFK(q0, tool_pose).Pos()
p_fk_base = (base_pose * robot.SolveFK(q0, tool_pose)).Pos()
print("PoseAbs          :", [round(v, 2) for v in p_abs])
print("SolveFK(裸)      :", [round(v, 2) for v in p_fk_flange])
print("base*SolveFK     :", [round(v, 2) for v in p_fk_base])
print("base*SolveFK 偏差 mm :", round(max(abs(a - b) for a, b in zip(p_abs, p_fk_base)), 4))

q1 = list(q0)
q1[0] += 20.0
pts = []
import time
t0 = time.perf_counter()
N = 20
for i in range(N + 1):
    q = [a + (b - a) * i / N for a, b in zip(q0, q1)]
    pts.append(list((base_pose * robot.SolveFK(q, tool_pose)).Pos()))
dt = (time.perf_counter() - t0) / (N + 1) * 1000
print("FK 采样 %d 点，平均 %.2f ms/点" % (N + 1, dt))
print("首点:", [round(v, 1) for v in pts[0]], " 末点:", [round(v, 1) for v in pts[-1]])
seg = [((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2) ** .5 for a, b in zip(pts, pts[1:])]
print("相邻点距 mm: min %.1f max %.1f（平滑=无跳变）" % (min(seg), max(seg)))

mat = robomath.Mat(pts).tr()
curve = RDK.AddCurve(mat, None, False, 0)
curve.setName("_probe28_测试曲线")
curve.setColorCurve([1.0, 0.82, 0.0, 1.0])
print("curve:", curve.Name(), curve.Valid())
curve.Delete()
print("已删除")
