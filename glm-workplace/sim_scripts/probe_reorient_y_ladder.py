# -*- coding: utf-8 -*-
"""只读：换姿过渡点 y 梯探针——P6→P7（rx90→rx180）与 P13→P14（rx180/180→rx90/90）
在 z=380、各 y 候选上的：两态静态碰撞 + 换姿 MoveL（原位姿态插补）+ MoveJ 备选路径。
取离锚点（≈−700）最近的全绿 y。
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk.robolink import *
from robodk.robomath import Fanuc_2_Pose

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
frame = robot.PoseFrame()
tool = Fanuc_2_Pose([0.0, 0.0, 182.0, 0.0, 0.0, 0.0])
J4MAX, J5MIN = 100.0, 165.0

RDK.setRunMode(RUNMODE_SIMULATE)
RDK.setCollisionActive(True)
for name in ('安装台_650x650x80mm', '地面_禁止穿越', '磨砂圆柱_R150_H50', '挡板_半封闭3面'):
    obstacle = RDK.Item(name, ITEM_TYPE_OBJECT)
    if name == '安装台_650x650x80mm':
        RDK.setCollisionActivePair(COLLISION_OFF, robot, obstacle, 0, 0)
    for link in range(1, 7):
        RDK.setCollisionActivePair(COLLISION_ON, robot, obstacle, link, 0)
_h = RDK.Item('门把手_bs1')
for link in range(1, 7):
    RDK.setCollisionActivePair(1, robot, _h, link, 0)

def all_ik(vals):
    q = robot.SolveIK_All(Fanuc_2_Pose([float(v) for v in vals]), tool=tool, reference=frame)
    try:
        rows = q.rows
    except Exception:
        return []
    if not rows or len(rows) < 6:
        return []
    out = []
    for c in range(len(rows[0])):
        sol = [rows[r][c] for r in range(6)]
        if abs(sol[3]) > J4MAX and abs(sol[4]) > J5MIN:
            continue
        out.append(sol)
    return out

def stat(q):
    return robot.MoveJ_Test(q, q, minstep_deg=1) == 0

def test_pair(x, y, z, a, b):
    """返回 (换姿MoveL可行, MoveJ可行, 静态双绿) —— 取第一对无碰分支组合"""
    As = all_ik([x, y, z] + list(a))
    Bs = all_ik([x, y, z] + list(b))
    if not As or not Bs:
        return None, None, False
    pose_b = Fanuc_2_Pose([float(v) for v in ([x, y, z] + list(b))])
    line_ok = False; mj_ok = False; stat_ok = False
    for qa in As:
        if not stat(qa):
            continue
        stat_ok = True
        for qb in Bs:
            if not stat(qb):
                continue
            if not line_ok:
                st = robot.MoveL_Test(qa, pose_b, minstep_mm=1)
                line_ok = (st == 0)
            if not mj_ok and robot.MoveJ_Test(qa, qb, minstep_deg=3) == 0:
                mj_ok = True
            if line_ok or mj_ok:
                return line_ok, mj_ok, stat_ok
    return line_ok, mj_ok, stat_ok

print('=== 槽1：rx90 → rx180（P6→P7 换姿），x=0 z=380 ===')
s1 = None
for y in (-712.5, -690.0, -670.0, -650.0, -630.0, -610.0, -590.0, -560.0):
    line, mj, st = test_pair(0, y, 380, (90, 0, 0), (180, 0, 0))
    print('y=%-8.1f 静态%s  MoveL换姿%s  MoveJ备选%s' % (
        y, '绿' if st else '✗', line, mj))
    if st and (line or mj):
        s1 = y
        print('  → 槽1 采用 y=%.1f（离面 %.0fmm）' % (y, y - (-720.0)))
        break

print('=== 槽2：(180,180) → (90,90)（P13→P14 换姿），x=20 z=380 ===')
s2 = None
for y in (-700.0, -690.0, -670.0, -650.0, -630.0, -610.0, -590.0, -560.0):
    line, mj, st = test_pair(20, y, 380, (180, 0, 180), (90, 0, 90))
    print('y=%-8.1f 静态%s  MoveL换姿%s  MoveJ备选%s' % (
        y, '绿' if st else '✗', line, mj))
    if st and (line or mj):
        s2 = y
        print('  → 槽2 采用 y=%.1f（离面 %.0fmm）' % (y, y - (-720.0)))
        break

print('RESULT 槽1=%s 槽2=%s' % (s1, s2))
print('DONE（只读）')
