# -*- coding: utf-8 -*-
"""接触位形验证（临时 SIMULATE，finally 恢复原 RunMode 与关节）：
1) 圆柱 y: -926 → -915（R140 近面 = y_c+140 = -775 = 轨迹11 工作线）
2) TCP (0,-775,470,-90,0,180)（负侧工作姿态）：IK + 与圆柱碰撞
3) TCP (0,-775,470,-90,0,0)（字面姿态）：IK + 与圆柱碰撞（预期法兰探入=碰撞）
4) 停在工作姿态接触位形截图 → 恢复原关节/RunMode
不保存工作站。"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import *
from robodk.robomath import *

RDK = Robolink()
ORIG_RUNMODE = RDK.RunMode()
print('原 RunMode = %r（6=RUN_ROBOT 实机直连）' % ORIG_RUNMODE)
if ORIG_RUNMODE not in (RUNMODE_SIMULATE, RUNMODE_RUN_ROBOT):
    raise SystemExit('中止：未知 RunMode %r，不动关节。' % ORIG_RUNMODE)
RDK.setRunMode(RUNMODE_SIMULATE)
print('已临时切 SIMULATE ✓')

robot = RDK.Item('', ITEM_TYPE_ROBOT)
assert robot.Valid(), '未找到机器人'
q0 = robot.Joints().list()[:]           # 保存原关节
print('原关节 =', ['%.3f' % v for v in q0])

try:
    # ---- 1) 圆柱挪到 y=-915 ----
    cyl = RDK.Item('磨砂圆柱_R150_H50', ITEM_TYPE_OBJECT)
    assert cyl.Valid(), '未找到圆柱'
    P = cyl.Pose()
    print('圆柱旧位姿 t=(%.3f, %.3f, %.3f)' % (P[0, 3], P[1, 3], P[2, 3]))
    P[1, 3] = -915.0
    cyl.setPose(P)
    P = cyl.Pose()
    print('圆柱新位姿 t=(%.3f, %.3f, %.3f)  近面 y=%.1f（= y_c+140）' % (P[0, 3], P[1, 3], P[2, 3], P[1, 3] + 140))

    # 碰撞配对：机器人各连杆 + 门把手 与 圆柱
    ok_all = True
    for link in range(0, 7):
        r = RDK.setCollisionActivePair(COLLISION_ON, robot, cyl, link, 0)
        ok_all = ok_all and (r == 1)
    handle = RDK.Item('门把手_bs1')
    if handle.Valid():
        r = RDK.setCollisionActivePair(COLLISION_ON, handle, cyl)
        ok_all = ok_all and (r == 1)
    print('碰撞配对启用 =', ok_all)
    RDK.setCollisionActive(COLLISION_ON)

    def test_pose(label, fanuc):
        pose = Fanuc_2_Pose(fanuc)                      # 目标 TCP（基座系）
        flange_target = pose * invH(robot.PoseTool())   # SolveIK 解的是法兰
        q = robot.SolveIK(flange_target)
        if q is None or len(q.list()) < 6:
            print('%s: IK 失败（q=%r）' % (label, q))
            return None
        ql = q.list()[:6]
        # FK 回代误差（TCP，位姿矩阵逐元素）
        tcp = robot.SolveFK(q) * robot.PoseTool()
        err = max(abs(tcp[i, j] - pose[i, j]) for i in range(4) for j in range(4))
        if err > 1e-3:
            print('%s: IK 回代超差（%.3f），视为失败，不动关节' % (label, err))
            return None
        robot.setJoints(q)
        col_robot = robot.Collision(cyl)
        col_handle = handle.Collision(cyl) if handle.Valid() else None
        print('%s: IK关节=[%s] FK回代误差=%.4f  机器人-圆柱碰撞=%s  门把手-圆柱碰撞=%s' % (
            label, ', '.join('%.1f' % v for v in ql), err, col_robot, col_handle))
        return ql

    print('--- 接触位形测试（TCP=(0,-775,470)）---')
    q180 = test_pose('(-90,0,180) 工作姿态', (0, -775, 470, -90, 0, 180))
    q0oo = test_pose('(-90,0,0)  字面姿态', (0, -775, 470, -90, 0, 0))

    # ---- 截图：停在工作姿态接触位形（若 IK 成功）----
    SHOT = r'D:\mydata\glm-workplace\tools\rdk_contact_check.png'
    if q180:
        robot.setJoints(q180)
        RDK.Render(True)
        if os.path.exists(SHOT):
            os.remove(SHOT)
        r = RDK.Cam2D_Snapshot(SHOT, None)
        print('接触位形截图 -> %s (ret=%r, %d bytes)' % (
            SHOT, r, os.path.getsize(SHOT) if os.path.exists(SHOT) else -1))
finally:
    robot.setJoints(q0)
    RDK.setRunMode(ORIG_RUNMODE)
    print('已恢复原关节与 RunMode = %r' % ORIG_RUNMODE)
    print('DONE（未保存工作站；圆柱留在 y=-915）')
