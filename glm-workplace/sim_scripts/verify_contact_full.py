# -*- coding: utf-8 -*-
"""完整接触验证：
A) 负侧：圆柱 y=-915（近面=-775=轨迹11工作线），TCP(0,-775,470,-90,0,180)
   —— 摆到接触位形截图（setJoints 必须传 6×1 Mat，扁平 list 只写 J1）；
B) 正侧镜像：圆柱临时 y=+915，TCP(0,+775,470,-90,0,0) —— IK/限位/碰撞/截图；
C) 结束时圆柱放回 y=-915，关节/RunMode 恢复原状。"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import *
from robodk.robomath import *

RDK = Robolink()
ORIG_RUNMODE = RDK.RunMode()
RDK.setRunMode(RUNMODE_SIMULATE)
robot = RDK.Item('', ITEM_TYPE_ROBOT)
q0m = robot.Joints()
cyl = RDK.Item('磨砂圆柱_R150_H50', ITEM_TYPE_OBJECT)
handle = RDK.Item('门把手_bs1')
LIM = (180, 180, 160, 190, 180, 360)
print('原关节=%s RunMode=%r' % (['%.1f' % v for v in q0m.list()[:6]], ORIG_RUNMODE))

def setq(qlist):
    robot.setJoints(Mat([[v] for v in qlist]))    # 6×1 列矩阵

def enable_pairs():
    ok = True
    for link in range(0, 7):
        ok = ok and (RDK.setCollisionActivePair(COLLISION_ON, robot, cyl, link, 0) == 1)
    if handle.Valid():
        ok = ok and (RDK.setCollisionActivePair(COLLISION_ON, handle, cyl) == 1)
    RDK.setCollisionActive(COLLISION_ON)
    return ok

def ik_all(fanuc):
    pose = Fanuc_2_Pose(fanuc)
    fl = pose * invH(robot.PoseTool())
    sols = robot.SolveIK_All(fl) or []
    valid = []
    for q in sols:
        ql = list(q)[:6]
        tcp = robot.SolveFK(q) * robot.PoseTool()
        err = max(abs(tcp[a, b] - pose[a, b]) for a in range(4) for b in range(4))
        if err < 1e-3 and all(abs(v) <= L + 1e-6 for v, L in zip(ql, LIM)):
            valid.append(ql)
    return valid

def place_cyl(y):
    P = cyl.Pose(); P[1, 3] = y; cyl.setPose(P)

try:
    print('碰撞配对 =', enable_pairs())

    # ---------- A) 负侧 y=-915 ----------
    place_cyl(-915.0)
    solsA = ik_all((0, -775, 470, -90, 0, 180))
    print('A) 负侧 (-90,0,180): 限位内有效解 %d 个' % len(solsA))
    assert solsA, 'A 侧无解?!'
    setq(solsA[0])
    print('   摆位后读回 =', ['%.1f' % v for v in robot.Joints().list()[:6]])
    print('   机器人-圆柱碰撞=%s 门把手-圆柱碰撞=%s（0=仅贴合不穿透）' % (
        robot.Collision(cyl), handle.Collision(cyl) if handle.Valid() else None))
    RDK.Render(True)
    SHOT = r'D:\mydata\glm-workplace\tools\rdk_contact_neg.png'
    if os.path.exists(SHOT): os.remove(SHOT)
    r = RDK.Cam2D_Snapshot(SHOT, None)
    print('   截图 ret=%r %d bytes 读回=%s' % (r, os.path.getsize(SHOT),
          ['%.1f' % v for v in robot.Joints().list()[:6]]))

    # ---------- B) 正侧 y=+915（字面 -90,0,0） ----------
    place_cyl(915.0)
    solsB = ik_all((0, 775, 470, -90, 0, 0))
    print('B) 正侧 (-90,0,0) @ TCP(0,775,470): 限位内有效解 %d 个' % len(solsB))
    if solsB:
        setq(solsB[0])
        print('   示例解 [%s]' % ', '.join('%.1f' % v for v in solsB[0]))
        print('   机器人-圆柱碰撞=%s 门把手-圆柱碰撞=%s' % (
            robot.Collision(cyl), handle.Collision(cyl) if handle.Valid() else None))
        SHOT2 = r'D:\mydata\glm-workplace\tools\rdk_contact_pos.png'
        if os.path.exists(SHOT2): os.remove(SHOT2)
        r2 = RDK.Cam2D_Snapshot(SHOT2, None)
        print('   截图 ret=%r %d bytes' % (r2, os.path.getsize(SHOT2)))
    place_cyl(-915.0)
    print('圆柱已放回 y=-915')
finally:
    robot.setJoints(q0m)
    RDK.setRunMode(ORIG_RUNMODE)
    print('已恢复 关节=%s RunMode=%r' % (['%.1f' % v for v in robot.Joints().list()[:6]], ORIG_RUNMODE))
