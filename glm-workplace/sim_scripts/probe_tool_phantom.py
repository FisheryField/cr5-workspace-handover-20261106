# -*- coding: utf-8 -*-
"""只读验证「单位变换幽灵碰撞」假说：
同一组关节下，PoseTool=182 与 PoseTool=identity 各测一次碰撞，
再测真实直线中点(x=0)与 P4→P5 关节弧中点。结束恢复工具/关节/runmode。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose, invH

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
assert robot.Valid()
start_q = robot.Joints().list()[:6]
start_tool = robot.PoseTool()

def pose_collide(q):
    return robot.MoveJ_Test(q, q, minstep_deg=1) != 0

q_frozen = [67.51, 25.14, 113.89, -139.03, -67.51, 180.0]
P4Q = [84.550733, 26.060110, 112.249212, -138.309322, -84.550733, 180.0]
P5Q = [58.743710, 26.060110, 112.249212, -138.309322, -58.743710, 180.0]
q_arc50 = [(a + b) / 2.0 for a, b in zip(P4Q, P5Q)]

robot.setJoints([0.0] * 6)
RDK.setRunMode(robolink.RUNMODE_SIMULATE)

# 真实直线中点 (0,-719,380,rx90) 的关节（用 182 工具解）
robot.setPoseTool(start_tool)
T = Fanuc_2_Pose([0.0, -719.0, 380.0, 90.0, 0.0, 0.0])
flange = robot.PoseFrame() * T * invH(robot.PoseTool())
sols = robot.SolveIK_All(flange).tolist()
if sols and isinstance(sols[0], (int, float)):
    sols = [sols]
q_line = None
if sols:
    cand0 = sols[0][:6]
    q_line = [min((v + 360 * k for k in range(-3, 4)), key=lambda a: abs(a - P5Q[j]))
              for j, v in enumerate(cand0)]
print('q_line(x=0 中点) =', [round(v, 2) for v in (q_line or [])])

robot.setPoseTool(start_tool)   # 182
print('【tool=182】冻结姿态碰撞 =', pose_collide(q_frozen))
if q_line:
    print('【tool=182】直线中点碰撞 =', pose_collide(q_line))
print('【tool=182】关节弧50%%碰撞 =', pose_collide(q_arc50))

robot.setPoseTool(Fanuc_2_Pose([0, 0, 0, 0, 0, 0]))   # 单位变换
print('【tool=identity】冻结姿态碰撞 =', pose_collide(q_frozen))
if q_line:
    print('【tool=identity】直线中点碰撞 =', pose_collide(q_line))

robot.setPoseTool(start_tool)
robot.setJoints(start_q)
RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
print('DONE（工具/关节/runmode 已恢复）')
