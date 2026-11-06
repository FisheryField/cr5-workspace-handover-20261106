# -*- coding: utf-8 -*-
"""演示（只动模型显示）：把手外侧面贴圆柱的【可达】接触位姿——工具横放方案。
TCP 面法向压向圆柱(0,-1,0)；ẑ→世界(-1,0,0)（法兰在 +X 侧）；工作点 (0,-772,380)。
切 SIMULATE 摆位；完成后模型停留供查看；调用方喊停后再复位。"""
import sys, io, os, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose, Mat, invH

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
assert robot.Valid()

# 目标旋转：x̂=(0,0,-1), ŷ=(0,-1,0), ẑ=(-1,0,0)
xw, yw, zw = (0.0, 0.0, -1.0), (0.0, -1.0, 0.0), (-1.0, 0.0, 0.0)
m = Mat(4, 4)
axes = (xw, yw, zw)
for i in range(3):
    for j in range(3):
        m[i, j] = axes[j][i]
m[0, 3] = 0.0
m[1, 3] = -759.7
m[2, 3] = 380.0

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_head', 'exec'), ns)
fan = [float(v) for v in ns['pose_to_fanuc_values'](m)[:6]]
print('接触 TCP Fanuc = [%.2f, %.2f, %.2f, %.2f, %.2f, %.2f]' % tuple(fan))

RDK.setRunMode(robolink.RUNMODE_SIMULATE)
robot.setJoints([0.0] * 6)

flange = robot.PoseFrame() * m * invH(robot.PoseTool())
sols = robot.SolveIK_All(flange).tolist()
if sols and isinstance(sols[0], (int, float)):
    sols = [sols]
print('IK 解数 =', len(sols))
if not sols:
    RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
    raise SystemExit('该姿态仍无解')

q = [float(v) for v in min(sols, key=lambda s: abs(float(s[1])) )[:6]]
print('关节 =', ['%.2f' % v for v in q])
r = robot.MoveJ_Test(q, q, minstep_deg=1)
print('位姿碰撞检查 =', '碰撞!' if r != 0 else '无碰撞')

robot.setJoints(q)

OUT = r'D:\mydata\glm-workplace\tools\contact_pose_demo.png'
if os.path.exists(OUT):
    os.remove(OUT)
try:
    RDK.Cam2D_Snapshot(OUT, None)
except Exception:
    RDK.Cam2D_Snapshot(OUT, 0)
print('截图 =', OUT if os.path.exists(OUT) else '失败')
print('模型已停在横放贴面位姿（SIMULATE）。看完喊我复位。')
