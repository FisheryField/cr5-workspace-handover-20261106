# -*- coding: utf-8 -*-
"""实测真贴合深度：姿态固定 (0,-90,180)，TCP y 从 -695 逐步推向 -715，
MoveJ_Test 首次碰撞的 y = 实际触碰深度；再退 0.2mm 作为贴面演示位并摆模型。"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose, invH

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)

def solve(y):
    T = Fanuc_2_Pose([0.0, y, 380.0, 0.0, -90.0, 180.0])
    fl = robot.PoseFrame() * T * invH(robot.PoseTool())
    s = robot.SolveIK_All(fl).tolist()
    if s and isinstance(s[0], (int, float)):
        s = [s]
    return ([float(v) for v in s[0][:6]] if s else None)

RDK.setRunMode(robolink.RUNMODE_SIMULATE)
print('y       IK    碰撞')
first_hit = None
y = -695.0
while y >= -715.5:
    q = solve(y)
    if q is None:
        print('%7.1f  无解' % y)
        y -= 1.0
        continue
    hit = robot.MoveJ_Test(q, q, minstep_deg=1) != 0
    print('%7.1f  ok    %s' % (y, '碰撞' if hit else '—'))
    if hit and first_hit is None:
        first_hit = y
        break
    y -= 1.0

if first_hit is None:
    print('推到 -715 仍未碰——需检查面/滚轮假设')
else:
    y_touch = first_hit
    y_demo = y_touch + 0.3   # 退 0.3mm 贴面演示
    q = solve(y_demo)
    print('\n实测触碰深度 y ≈ %.1f ；演示位 y=%.1f（退 0.3mm）' % (y_touch, y_demo))
    r = robot.MoveJ_Test(q, q, minstep_deg=1)
    print('演示位碰撞检查 =', '碰撞!' if r != 0 else '无碰撞')
    robot.setJoints(q)
    print('演示关节 =', ['%.2f' % v for v in q])
    OUT = r'D:\mydata\glm-workplace\tools\contact_pose_demo.png'
    if os.path.exists(OUT):
        os.remove(OUT)
    try:
        RDK.Cam2D_Snapshot(OUT, None)
    except Exception:
        RDK.Cam2D_Snapshot(OUT, 0)
    print('截图 =', OUT if os.path.exists(OUT) else '失败')
print('DONE（SIMULATE 停在演示位）')
