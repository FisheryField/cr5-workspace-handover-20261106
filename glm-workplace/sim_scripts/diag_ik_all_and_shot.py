# -*- coding: utf-8 -*-
"""诊断：(1) SolveIK_All 复核 (-90,0,0)/(-90,0,180) 是否有解；
(2) setJoints 后立刻读回 + 截图（查场景是否被连接同步拽回家位）。"""
import sys, io, os, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import *
from robodk.robomath import *

RDK = Robolink()
ORIG_RUNMODE = RDK.RunMode()
RDK.setRunMode(RUNMODE_SIMULATE)
robot = RDK.Item('', ITEM_TYPE_ROBOT)
q0 = robot.Joints().list()[:]
print('原关节 =', ['%.3f' % v for v in q0], ' 原RunMode=%r' % ORIG_RUNMODE)

LIM = (180, 180, 160, 190, 180, 360)   # 实机关限

def in_limits(q):
    return all(abs(v) <= L + 1e-6 for v, L in zip(q, LIM))

def show_all(label, fanuc):
    pose = Fanuc_2_Pose(fanuc)
    flange_target = pose * invH(robot.PoseTool())
    sols = robot.SolveIK_All(flange_target)
    print('%s: SolveIK_All 解数 = %s' % (label, len(sols) if sols is not None else 'None'))
    good = 0
    for i, q in enumerate(sols or []):
        ql = list(q)[:6]
        tcp = robot.SolveFK(q) * robot.PoseTool()
        err = max(abs(tcp[a, b] - pose[a, b]) for a in range(4) for b in range(4))
        ok = err < 1e-3
        if ok:
            good += 1
        print('  解%-2d [%s] 回代=%s 实机限位=%s' % (
            i + 1, ', '.join('%.1f' % v for v in ql),
            'OK' if ok else 'ERR%.2f' % err, in_limits(ql) if ok else '-'))
    print('  => 有效解 %d 个' % good)
    return sols

try:
    show_all('TCP(0,-775,470) (-90,0,180)', (0, -775, 470, -90, 0, 180))
    show_all('TCP(0,-775,470) (-90,0,0)  ', (0, -775, 470, -90, 0, 0))

    # setJoints 读回诊断
    sols = robot.SolveIK_All(Fanuc_2_Pose((0, -775, 470, -90, 0, 180)) * invH(robot.PoseTool()))
    q180 = sols[0]
    robot.setJoints(q180)
    print('setJoints 后立即读回 =', ['%.1f' % v for v in robot.Joints().list()[:6]])
    time.sleep(1.0)
    print('1秒后再读回        =', ['%.1f' % v for v in robot.Joints().list()[:6]])
    RDK.Render(True)
    SHOT = r'D:\mydata\glm-workplace\tools\rdk_contact_check2.png'
    if os.path.exists(SHOT):
        os.remove(SHOT)
    r = RDK.Cam2D_Snapshot(SHOT, None)
    after = robot.Joints().list()[:6]
    print('截图 ret=%r bytes=%d 截图时关节=[%s]' % (
        r, os.path.getsize(SHOT) if os.path.exists(SHOT) else -1,
        ', '.join('%.1f' % v for v in after)))
finally:
    robot.setJoints(q0)
    RDK.setRunMode(ORIG_RUNMODE)
    print('已恢复 关节=%s RunMode=%r' % (['%.1f' % v for v in robot.Joints().list()[:6]], ORIG_RUNMODE))
