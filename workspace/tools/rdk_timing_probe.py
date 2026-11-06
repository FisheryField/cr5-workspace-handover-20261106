#!/usr/bin/env python3
"""只读计时探针：量化 机械臂TCP仿真.py 预检阶段各 API 的单次开销。
纯仿真侧计算（Test/IK/FK 不产生任何物理运动），结束后恢复关节状态。"""
import time

from robodk.robolink import *
from robodk.robomath import *

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
print('robot:', robot.Name(), '| RunMode:', RDK.RunMode())

q0 = robot.Joints().list()[:6]
print('q0:', [round(v, 3) for v in q0])

# ---- 1) COM 往返基线 & FK ----
N = 200
t0 = time.perf_counter()
for _ in range(N):
    robot.Joints()
t1 = time.perf_counter()
print('robot.Joints()        : %6.2f ms/次' % ((t1 - t0) / N * 1000))

t0 = time.perf_counter()
for _ in range(N):
    robot.SolveFK(q0)
t1 = time.perf_counter()
print('robot.SolveFK(q)      : %6.2f ms/次' % ((t1 - t0) / N * 1000))

t0 = time.perf_counter()
for _ in range(50):
    robot.JointPoses(q0)
t1 = time.perf_counter()
print('robot.JointPoses(q)   : %6.2f ms/次' % ((t1 - t0) / 50 * 1000))

t0 = time.perf_counter()
for _ in range(50):
    robot.PoseFrame(); robot.PoseTool()
t1 = time.perf_counter()
print('PoseFrame+PoseTool    : %6.2f ms/次(两调用)' % ((t1 - t0) / 50 * 1000))

# ---- 2) MoveL_Test 步长密度 ----
flange = robot.SolveFK(q0)
target50 = flange * transl(0, 0, -50)   # 沿工具Z走50mm
for step_mm in (10.0, 5.0, 1.0):
    t0 = time.perf_counter()
    st = robot.MoveL_Test(q0, target50, minstep_mm=step_mm)
    t1 = time.perf_counter()
    print('MoveL_Test 50mm @%-4.0fmm: status=%s  %6.0f ms' % (step_mm, st, (t1 - t0) * 1000))
    robot.setJoints(q0)

# ---- 3) MoveJ_Test 步长密度 ----
end20 = q0[:]; end20[0] += 20.0
for step_deg in (1.0, 0.25):
    t0 = time.perf_counter()
    st = robot.MoveJ_Test(q0, end20, minstep_deg=step_deg)
    t1 = time.perf_counter()
    print('MoveJ_Test 20°  @%-4.2f° : status=%s  %6.0f ms' % (step_deg, st, (t1 - t0) * 1000))
    robot.setJoints(q0)

# ---- 4) InstructionListJoints（_linear_path_endpoint/_verify_obstacle_plan 用）----
prog = RDK.AddProgram('_timing_probe', robot)
try:
    prog.setVisible(False)
    prog.setPoseFrame(robot.PoseFrame())
    prog.setPoseTool(robot.PoseTool())
    prog.MoveJ(q0)
    prog.MoveL(target50)
    for mmstep in (5.0, 1.0):
        t0 = time.perf_counter()
        msg, mat, status = prog.InstructionListJoints(mm_step=mmstep, deg_step=mmstep, collision_check=COLLISION_OFF)
        t1 = time.perf_counter()
        try:
            nr = mat.tr().rows
        except Exception:
            nr = []
        print('InstructionListJoints @%-2.0fmm/°: status=%s rows=%d  %6.0f ms (碰撞检查关)' %
              (mmstep, status, len(nr), (t1 - t0) * 1000))
    for mmstep, cc in ((1.0, COLLISION_OFF), (1.0, COLLISION_ON), (5.0, COLLISION_ON)):
        t0 = time.perf_counter()
        msg, mat, status = prog.InstructionListJoints(mm_step=mmstep, deg_step=mmstep, collision_check=cc)
        t1 = time.perf_counter()
        try:
            n = len(mat.tr().rows)
        except Exception:
            n = 0
        print('InstructionListJoints @%-2.0fmm/° collision=%s: status=%s rows=%d  %6.0f ms' %
              (mmstep, 'ON' if cc else 'OFF', status, n, (t1 - t0) * 1000))
finally:
    prog.Delete()
    robot.setJoints(q0)

print('done. joints restored:', [round(v, 3) for v in robot.Joints().list()[:6]])
