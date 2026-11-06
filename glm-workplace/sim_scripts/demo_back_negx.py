# -*- coding: utf-8 -*-
"""模型摆回 x=-1.163 的极限位（上一位置 -10mm）。"""
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

X = -11.163
T = from_fanuc(X, -685.000, 382.666, -88.938, -59.662, -90.931)
fl = robot.PoseFrame() * T * invH(robot.PoseTool())
s = robot.SolveIK_All(fl).tolist()
if s and isinstance(s[0], (int, float)):
    s = [s]
assert s, '无解'
Q_REF = [56.540, 99.342, -40.809, -57.560, 33.450, -60.478]
q = [float(v) for v in min(s, key=lambda sol: sum((float(sol[j]) - Q_REF[j]) ** 2 for j in range(6)))[:6]]
hit = robot.MoveJ_Test(q, q, minstep_deg=1) != 0
print('TCP = (%.3f, -685.000, 382.666, -88.938, -59.662, -90.931)' % X)
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
print('DONE（模型已摆位，SIMULATE）')
