# -*- coding: utf-8 -*-
"""真实几何下的贴合验证+演示：滚轮心(0,-860,380) R150，赤道面 y=-710@z=380。
贴合 TCP=(0,-697.7,380)，姿态=面法向朝滚轮（φ=0 解 [0,-90,180]，等价 P19[90,0,90]+J6±90）。
IK/碰撞检查后摆模型+截图。"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose, invH

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)

RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
print('runmode 已复位 RUN_ROBOT')

def ik(name, x, y, z, rx, ry, rz):
    T = Fanuc_2_Pose([x, y, z, rx, ry, rz])
    fl = robot.PoseFrame() * T * invH(robot.PoseTool())
    s = robot.SolveIK_All(fl).tolist()
    if s and isinstance(s[0], (int, float)):
        s = [s]
    print('%s -> %s' % (name, '%d 解' % len(s) if s else '无解'))
    return s

s = ik('贴合位 (0,-697.7,380, 0,-90,180)', 0.0, -697.7, 380.0, 0.0, -90.0, 180.0)
ik('P19 对照 (35,-699,380, 90,0,90)', 35.0, -699.0, 380.0, 90.0, 0.0, 90.0)

if s:
    sol = s[0]
    q = [float(v) for v in sol[:6]]
    print('贴合位关节 =', ['%.2f' % v for v in q])
    RDK.setRunMode(robolink.RUNMODE_SIMULATE)
    r = robot.MoveJ_Test(q, q, minstep_deg=1)
    print('碰撞检查 =', '碰撞!' if r != 0 else '无碰撞')
    if r != 0:
        T2 = Fanuc_2_Pose([0.0, -697.2, 380.0, 0.0, -90.0, 180.0])
        fl2 = robot.PoseFrame() * T2 * invH(robot.PoseTool())
        s2 = robot.SolveIK_All(fl2).tolist()
        if s2 and isinstance(s2[0], (int, float)):
            s2 = [s2]
        if s2:
            q = [float(v) for v in s2[0][:6]]
            print('退 0.5mm 后碰撞 =', '碰撞!' if robot.MoveJ_Test(q, q, minstep_deg=1) != 0 else '无碰撞（贴面演示位）')
    robot.setJoints(q)
    OUT = r'D:\mydata\glm-workplace\tools\contact_pose_demo.png'
    if os.path.exists(OUT):
        os.remove(OUT)
    try:
        RDK.Cam2D_Snapshot(OUT, None)
    except Exception:
        RDK.Cam2D_Snapshot(OUT, 0)
    print('截图 =', OUT if os.path.exists(OUT) else '失败')
    print('模型已停在贴合演示位（SIMULATE）。看完喊我复位。')
print('DONE')
