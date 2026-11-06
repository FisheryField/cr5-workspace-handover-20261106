# -*- coding: utf-8 -*-
"""演示（只动模型显示，不碰实机）：把机器人模型摆到「把手外侧面贴圆柱」的接触位姿
TCP=(0,-759.7,380,180,0,0)，截图 RoboDK 视图。切 RUNMODE_SIMULATE 防驱动回拽模型；
结束后由调用方决定何时恢复 RUN_ROBOT（恢复即自动回实机姿态）。"""
import sys, io, os, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose, invH

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
assert robot.Valid()
start_q = robot.Joints().list()[:6]
print('当前模型关节 =', ['%.2f' % v for v in start_q])

RDK.setRunMode(robolink.RUNMODE_SIMULATE)
robot.setJoints([0.0] * 6)

T = Fanuc_2_Pose([0.0, -759.7, 380.0, 180.0, 0.0, 0.0])
flange = robot.PoseFrame() * T * invH(robot.PoseTool())
sols = robot.SolveIK_All(flange).tolist()
if sols and isinstance(sols[0], (int, float)):
    sols = [sols]
print('IK 解数量 =', len(sols))
if not sols:
    robot.setJoints(start_q)
    RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
    raise SystemExit('接触位姿无逆解——检查可达性')

q = min(sols, key=lambda s: sum((float(s[j]) - start_q[j]) ** 2 for j in range(6)))[:6]
q = [float(v) for v in q]
print('选用关节 =', ['%.2f' % v for v in q])

r = robot.MoveJ_Test(q, q, minstep_deg=1)
print('接触位姿碰撞检查 =', '碰撞!' if r != 0 else '无碰撞')
if r != 0:
    # 相切可能被判穿透——TCP 沿 +Y 退 0.5mm 再试
    T2 = Fanuc_2_Pose([0.0, -759.2, 380.0, 180.0, 0.0, 0.0])
    fl2 = robot.PoseFrame() * T2 * invH(robot.PoseTool())
    s2 = robot.SolveIK_All(fl2).tolist()
    if s2 and isinstance(s2[0], (int, float)):
        s2 = [s2]
    if s2:
        q = [float(v) for v in min(s2, key=lambda s: sum((float(s[j]) - q[j]) ** 2 for j in range(6)))[:6]]
        r2 = robot.MoveJ_Test(q, q, minstep_deg=1)
        print('退 0.5mm 后 (0,-759.2,380) 碰撞 =', '碰撞!' if r2 != 0 else '无碰撞（贴面演示位）')

robot.setJoints(q)

OUT = r'D:\mydata\glm-workplace\tools\contact_pose_demo.png'
if os.path.exists(OUT):
    os.remove(OUT)
try:
    RDK.Cam2D_Snapshot(OUT, None)
except Exception:
    RDK.Cam2D_Snapshot(OUT, 0)
if os.path.exists(OUT):
    print('截图已存:', OUT, os.path.getsize(OUT), 'bytes')
print('模型已停在接触位姿（SIMULATE 态，实机不动）。看完喊我复位。')
