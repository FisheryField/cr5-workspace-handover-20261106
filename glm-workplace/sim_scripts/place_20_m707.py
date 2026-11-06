# -*- coding: utf-8 -*-
"""仅软件模型：摆到 (20,-707,380,90,0,90)。"""
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

T = from_fanuc(20.0, -707.0, 380.0, 90.0, 0.0, 90.0)
fl = robot.PoseFrame() * T * invH(robot.PoseTool())
s = robot.SolveIK_All(fl).tolist()
if s and isinstance(s[0], (int, float)):
    s = [s]
assert s, '无解'
# 全分支里取第一个无碰撞的；全撞则取最近解并如实报告
Q_REF = [float(v) for v in robot.Joints().list()[:6]] if len(robot.Joints().list()) >= 6 else [0.0]*6
q_pick, hit = None, None
for sol in sorted(s, key=lambda sol: sum((float(sol[j]) - Q_REF[j]) ** 2 for j in range(6))):
    q = [float(v) for v in sol[:6]]
    h = robot.MoveJ_Test(q, q, minstep_deg=1) != 0
    if not h:
        q_pick, hit = q, False
        break
    if q_pick is None:
        q_pick, hit = q, True
print('TCP = (20.000, -707.000, 380.000, 90.000, 0.000, 90.000)')
print('关节 =', ['%.3f' % v for v in q_pick])
print('碰撞检查 =', '碰撞!' if hit else '无碰撞')
robot.setJoints(q_pick)
OUT = r'D:\mydata\glm-workplace\tools\contact_pose_demo.png'
if os.path.exists(OUT):
    os.remove(OUT)
try:
    RDK.Cam2D_Snapshot(OUT, None)
except Exception:
    RDK.Cam2D_Snapshot(OUT, 0)
print('截图 =', OUT if os.path.exists(OUT) else '失败')
print('DONE（SIMULATE，实机未动）')
