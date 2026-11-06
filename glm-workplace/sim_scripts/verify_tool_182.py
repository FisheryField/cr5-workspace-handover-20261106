# -*- coding: utf-8 -*-
"""只读复核（2026-10-20）：PoseTool=182 已生效 + SolveIK 位姿语义正确验证。
RoboDK 语义（源码 robolink.py L5645）：
  SolveIK(pose, joints_approx=None, tool=None, reference=None)
  - 不带 tool：pose = 法兰位姿（相对 base）
  - 带 tool：pose = TCP 位姿（先 pose*invH(tool) 转法兰再解）
  - 无解时返回空矩阵（size 0），不是 None
"""
from robodk.robolink import *
from robodk.robomath import *
import math

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
if not robot.Valid():
    raise SystemExit('ERROR: 未找到机器人')

cur = Pose_2_Fanuc(robot.PoseTool())
print('当前 PoseTool:', ['%.3f' % v for v in cur])
assert abs(cur[2] - 182.0) < 1e-6, 'PoseTool 未是 182！'

frame = robot.PoseFrame()
tests = [
    ('[0,-775,300,90,0,0]', [0.0, -775.0, 300.0, 90.0, 0.0, 0.0]),
    ('[500,0,300,180,0,0]', [500.0, 0.0, 300.0, 180.0, 0.0, 0.0]),
    ('[0,-615,300,90,0,0]', [0.0, -615.0, 300.0, 90.0, 0.0, 0.0]),
]

ok = True
for name, vals in tests:
    T = Fanuc_2_Pose(vals)
    q = robot.SolveIK(T, tool=robot.PoseTool(), reference=frame)
    qv = list(q)
    if len(qv) < 6:
        print('%s -> 无解（空矩阵, len=%d）' % (name, len(qv)))
        ok = False
        continue
    # TCP 校验：宏 _trajectory_pose 同款
    tcp = invH(frame) * robot.SolveFK(q) * robot.PoseTool()
    flg = invH(frame) * robot.SolveFK(q)
    d_tcp = norm((invH(T) * tcp).Pos())
    d_flg = norm((invH(T) * flg).Pos())
    print('%s -> q=[%s]  d(TCP,T)=%.3f mm  d(Flange,T)=%.3f mm' % (
        name, ','.join('%.2f' % v for v in qv[:6]), d_tcp, d_flg))

# 无 tool 对照：同一 T 应被当法兰（TCP=法兰+182）
T2 = Fanuc_2_Pose(tests[1][1])
q2 = robot.SolveIK(T2)
qv2 = list(q2)
if len(qv2) >= 6:
    flg2 = robot.SolveFK(qv2)                 # base 系法兰
    print('对照 SolveIK(T) 不带 tool -> q=[%s]' % ','.join('%.2f' % v for v in qv2[:6]))
    print('  其法兰 vs T = %.3f mm（≈0 => 不带 tool 时 pose 即法兰）' %
          norm((invH(T2) * flg2).Pos()))

print('RESULT:', 'OK' if ok else 'HAS-FAIL（见上）')
print('DONE（只读，未发运动，未保存工作站）')
