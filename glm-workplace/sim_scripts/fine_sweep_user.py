# -*- coding: utf-8 -*-
"""精扫用户倾斜姿态的最近无碰撞 y（+20 ~ +32mm，0.5mm 步）。"""
import sys, io
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
Q_REF = [57.550, 94.750, -30.020, -63.730, 32.440, -60.510]
RDK.setRunMode(robolink.RUNMODE_SIMULATE)

found = None
dy = 20.0
while dy <= 32.01:
    y = -708.953 + dy
    T = from_fanuc(-1.163, y, 382.666, -88.938, -59.662, -90.931)
    fl = robot.PoseFrame() * T * invH(robot.PoseTool())
    s = robot.SolveIK_All(fl).tolist()
    if s and isinstance(s[0], (int, float)):
        s = [s]
    if s:
        q = [float(v) for v in min(s, key=lambda sol: sum((float(sol[j]) - Q_REF[j]) ** 2 for j in range(6)))[:6]]
        hit = robot.MoveJ_Test(q, q, minstep_deg=1) != 0
        if not hit:
            print('首个无碰撞：dy=+%.1fmm  y=%.3f' % (dy, y))
            print('  TCP = (-1.163, %.3f, 382.666, -88.938, -59.662, -90.931)' % y)
            print('  关节 =', ['%.3f' % v for v in q])
            found = dy
            break
    dy += 0.5
if not found:
    print('+20~+32 无解')
RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
print('DONE')
