# -*- coding: utf-8 -*-
"""只读探针：为「工具-朝上(rx0) 作业变体」寻找安全回撤位/换向路径（圆柱面已后移到 −822）。
- 激活障碍物碰撞对（与宏 _enable_obstacle_checks 同款）；
- 候选回撤位 R=(0,yR,470)：检查 q_R=IK(R,rx0) 的静态碰撞 + 与 q_W90=IK(W,rx90) 的 MoveJ 路径；
- 工作点 W=(0,-781,470)：检查 rx0 各滚转静态碰撞。
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk.robolink import *
from robodk.robomath import Fanuc_2_Pose

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
frame = robot.PoseFrame()
tool = Fanuc_2_Pose([0.0, 0.0, 182.0, 0.0, 0.0, 0.0])
W = (0.0, -781.0, 470.0)

RDK.setRunMode(RUNMODE_SIMULATE)
for name in ('安装台_650x650x80mm', '地面_禁止穿越', '磨砂圆柱_R150_H50', '挡板_半封闭3面'):
    obstacle = RDK.Item(name, ITEM_TYPE_OBJECT)
    if name == '安装台_650x650x80mm':
        RDK.setCollisionActivePair(COLLISION_OFF, robot, obstacle, 0, 0)
    for link in range(1, 7):
        RDK.setCollisionActivePair(COLLISION_ON, robot, obstacle, link, 0)
_h = RDK.Item('门把手_bs1')
for link in range(1, 7):
    RDK.setCollisionActivePair(1, robot, _h, link, 0)

def ik(x, y, z, rx, ry, rz, approx=None):
    kw = dict(tool=tool, reference=frame)
    if approx is not None:
        q = robot.SolveIK(Fanuc_2_Pose([float(x), float(y), float(z), float(rx), float(ry), float(rz)]),
                          approx, **kw)
    else:
        q = robot.SolveIK(Fanuc_2_Pose([float(x), float(y), float(z), float(rx), float(ry), float(rz)]), **kw)
    try:
        t = q.tolist()
    except Exception:
        t = []
    flat = []
    for v in t:
        flat.extend(v if isinstance(v, (list, tuple)) else [v])
    return flat[:6] if len(flat) >= 6 else None

def static_collide(q):
    return robot.MoveJ_Test(q, q, minstep_deg=1) != 0

def path_collide(qa, qb):
    return robot.MoveJ_Test(qa, qb, minstep_deg=2) != 0

print('=== W 工作点 rx0 族静态（圆柱面-822 后）===')
for rz in (0.0, 90.0, 180.0, -90.0):
    q = ik(W[0], W[1], W[2], 0, 0, rz)
    if q is None:
        print('W rx0 rz=%-5d IK 无解' % rz); continue
    print('W rx0 rz=%-5d 静态%s' % (rz, '碰撞✗' if static_collide(q) else 'OK✓'))

print('=== W rx90 静态 ===')
qW90 = ik(W[0], W[1], W[2], 90, 0, 0)
print('rx90:', '无解' if qW90 is None else ('碰撞✗' if static_collide(qW90) else 'OK✓'))

print('=== 回撤位 R 候选：静态(rx0) + 与 W(rx90) 的 MoveJ 路径 ===')
for yR in (-400.0, -450.0, -500.0, -550.0, -600.0, -650.0, -700.0):
    qR = ik(0, yR, 470, 0, 0, 0)
    if qR is None:
        print('R y=%-6.0f IK 无解' % yR); continue
    s = '静态碰撞✗' if static_collide(qR) else '静态OK'
    if qW90 is not None and not static_collide(qR):
        p = '路径碰撞✗' if path_collide(qW90, qR) else '路径OK✓'
    else:
        p = '路径-'
    print('R y=%-6.0f  %s  %s' % (yR, s, p))

print('=== 回撤位→W(rx0) 直线接近（MoveL_Test，第二参=目标位姿）===')
poseW0 = Fanuc_2_Pose([W[0], W[1], W[2], 0.0, 0.0, 0.0])
for yR in (-450.0, -500.0, -550.0, -600.0, -650.0):
    qR = ik(0, yR, 470, 0, 0, 0)
    if qR is None:
        print('yR=%-6.0f IK 缺' % yR); continue
    st = robot.MoveL_Test(qR, poseW0, minstep_mm=1)
    print('yR=%-6.0f MoveL_Test=%s' % (yR, 'OK✓' if st == 0 else '碰撞/不可行(%s)' % st))
print('DONE（只读，仿真模式）')
