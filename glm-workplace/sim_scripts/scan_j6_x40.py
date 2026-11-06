# -*- coding: utf-8 -*-
"""测三个 J6 旋转姿态在 x=40（滚轮端面外）各深度的全分支可行性。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import invH, rotz

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_head', 'exec'), ns)
fanuc_to_pose = ns['fanuc_values_to_pose']

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
RDK.setRunMode(robolink.RUNMODE_SIMULATE)

def any_clear(x, y, d):
    T = fanuc_to_pose(x, y, 380.0, 90.0, 0.0, 90.0) * rotz(d)
    fl = robot.PoseFrame() * T * invH(robot.PoseTool())
    s = robot.SolveIK_All(fl).tolist()
    if s and isinstance(s[0], (int, float)):
        s = [s]
    n_ok = 0
    for sol in s:
        q = [float(v) for v in sol[:6]]
        if robot.MoveJ_Test(q, q, minstep_deg=1) == 0:
            n_ok += 1
    return len(s), n_ok

for d in (90.0, 180.0, 270.0):
    for y in (-694.0, -700.0, -707.0):
        n_sol, n_ok = any_clear(40.0, y, d)
        print('x=40 J6+%-4g° y=%7.1f : %d解/%d无碰撞 -> %s' % (
            d, y, n_sol, n_ok, '可走' if n_ok else '碰撞'))
RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
print('DONE')
