# -*- coding: utf-8 -*-
"""确认 RoboDK 直发链路发给控制器的 6 参数用的是哪个欧拉约定（只读）。

对照控制器日志实录：
  P5 接受: (100.000000, -615.371000, 300.000000, -90.000000, 0.000000, -180.000000)
  P9 拒收: (-0.000000, -615.371000, 300.000000, 90.000000, 0.000000, -0.000000)
  单步接受: (0.000000, -615.371000, 299.999986, 89.999995, -0.000003, 0.000000)
输出 Pose_2_RPW 与 Pose_2_Fanuc 的结果（含符号位），判定约定。
"""
import sys, io, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Pose_2_Fanuc, Pose_2_TxyzRxyz, Pose_2_ABB, Pose_2_KUKA, \
    Pose_2_UR, Pose_2_Adept, Pose_2_Comau, Pose_2_Motoman, Pose_2_Nachi, \
    Pose_2_Staubli, Pose_2_Techman

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
assert robot.Valid(), '未找到机器人'
print('PoseFrame 是否单位阵：pos=%s (norm=%.6f)' % (robot.PoseFrame().Pos(), sum(v * v for v in robot.PoseFrame().Pos()) ** .5))
print('PoseTool：', robot.PoseTool().Pos())

J_P5 = [-63.41392174214573, -23.452600702069333, -86.65404121903774,
        -69.89335807889292, -63.41392174214573, -180.0]
J_P9 = [-74.10620847168758, -22.194417181878357, -88.53508496756278,
        -69.27049785055885, -74.10620847168758, -1.0507844097848867e-14]

def show(tag, vals):
    parts = []
    for v in vals:
        if v == 0.0 and math.copysign(1.0, v) < 0:
            parts.append('-0.000000(-0!)')
        else:
            parts.append('%.6f' % v)
    print('%-10s [%s]' % (tag, ', '.join(parts)))

for name, joints in (('P5', J_P5), ('P9', J_P9)):
    pose = robot.SolveFK(joints)   # 直发=工具置单位变换后 MoveL(joints) ⇒ 纯 FK
    print('===', name, '===')
    for fn in (Pose_2_TxyzRxyz, Pose_2_Fanuc, Pose_2_ABB, Pose_2_KUKA, Pose_2_UR,
               Pose_2_Adept, Pose_2_Comau, Pose_2_Motoman, Pose_2_Nachi,
               Pose_2_Staubli, Pose_2_Techman):
        show(fn.__name__.replace('Pose_2_', ''), fn(pose))
print('对照 P5 接受 (100,-615.371,300,-90,0,-180) / P9 拒收 (-0,-615.371,300,90,0,-0)')

# ---- 直接从旋转矩阵按几种约定反解 (r,p,w) 度，找与实录逐位吻合者 ----
import math
_p = robot.SolveFK(J_P5)
print('pose repr: rows=%d' % len(_p))
for _row in _p:
    print('   ', ['%.6f' % v for v in _row] if isinstance(_row, (list, tuple)) else _row)

def mat_of(pose):
    # pose 为 4x4：行可迭代出 float
    R = []
    for i, row in enumerate(pose):
        if i >= 3:
            break
        R.append([float(v) for v in list(row)[:3]])
    return R

def deg(x):
    return math.degrees(x)

def conv_RzRyRx(R):
    # R = Rz(w)·Ry(p)·Rx(r)
    p = -math.asin(max(-1.0, min(1.0, R[2][0])))
    r = math.atan2(R[2][1], R[2][2])
    w = math.atan2(R[1][0], R[0][0])
    return (deg(r), deg(p), deg(w))

def conv_RxRyRz(R):
    # R = Rx(r)·Ry(p)·Rz(w)
    p = math.asin(max(-1.0, min(1.0, R[0][2])))
    r = math.atan2(-R[1][2], R[2][2])
    w = math.atan2(-R[0][1], R[0][0])
    return (deg(r), deg(p), deg(w))

def conv_RzRxRy(R):
    # R = Rz(w)·Rx(r)·Ry(p)  (Fanuc ZYX 内旋的另一常见写法)
    # 略：用通用法不可靠，仅列两种
    return None

print()
for name, joints, expect in (('P5', J_P5, (-90.0, 0.0, -180.0)),
                             ('P9', J_P9, (90.0, 0.0, 0.0))):
    pose = robot.SolveFK(joints)
    R = mat_of(pose)
    a = conv_RzRyRx(R)
    b = conv_RxRyRz(R)
    print('%s 实录 rpw=(%.6f, %.6f, %.6f)' % (name, *expect))
    print('   RzRyRx: (%.6f, %.6f, %.6f)' % a)
    print('   RxRyRz: (%.6f, %.6f, %.6f)' % b)

