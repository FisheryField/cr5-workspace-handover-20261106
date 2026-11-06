# -*- coding: utf-8 -*-
"""仅软件模型：摆到 TCP=(35,-707,380,-82.287,85.925,-82.341)。"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import invH

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_head', 'exec'), ns)
from_fanuc = ns['fanuc_values_to_pose']

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
RDK.setRunMode(robolink.RUNMODE_SIMULATE)

Q_REF = [float(v) for v in robot.Joints().list()[:6]] if len(robot.Joints().list()) >= 6 else [0.0]*6
T = from_fanuc(35.0, -707.0, 380.0, -82.287, 85.925, -82.341)
fl = robot.PoseFrame() * T * invH(robot.PoseTool())
s = robot.SolveIK_All(fl).tolist()
if s and isinstance(s[0], (int, float)):
    s = [s]
assert s, '该位姿无逆解'
q = [float(v) for v in min(s, key=lambda sol: sum((float(sol[j]) - Q_REF[j]) ** 2 for j in range(6)))[:6]]
hit = robot.MoveJ_Test(q, q, minstep_deg=1) != 0
print('TCP = (35.000, -707.000, 380.000, -82.287, 85.925, -82.341)')
print('关节 =', ['%.3f' % v for v in q])
print('碰撞检查 =', '碰撞!' if hit else '无碰撞')
robot.setJoints(q)
OUT = r'D:\mydata\glm-workplace\tools\contact_pose_demo.png'
if os.path.exists(OUT):
    os.remove(OUT)
try:
    RDK.Cam2D_Snapshot(OUT, None)
except Exception:
    RDK.Cam2D_Snapshot(OUT, 0)
print('截图 =', OUT if os.path.exists(OUT) else '失败')
print('DONE（仅模型，SIMULATE；实机未动）')
