# -*- coding: utf-8 -*-
"""验证 (20,-707,380) 下 (90,0,90)/(90,0,180)/(90,0,270) 三姿态全分支可行性。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import invH

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_head', 'exec'), ns)
fanuc_to_pose = ns['fanuc_values_to_pose']
ns['_ensure_canonical_tool']()

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
RDK.setRunMode(robolink.RUNMODE_SIMULATE)

def any_clear(rz):
    T = fanuc_to_pose(20.0, -707.0, 380.0, 90.0, 0.0, float(rz))
    fl = robot.PoseFrame() * T * invH(robot.PoseTool())
    s = robot.SolveIK_All(fl).tolist()
    if s and isinstance(s[0], (int, float)):
        s = [s]
    n_ok = sum(1 for sol in s if robot.MoveJ_Test([float(v) for v in sol[:6]], [float(v) for v in sol[:6]], minstep_deg=1) == 0)
    return len(s), n_ok

for rz in (90.0, 180.0, 270.0):
    n_sol, n_ok = any_clear(rz)
    print('(90,0,%.0f) @ (20,-707) : %d解/%d无碰撞 -> %s' % (rz, n_sol, n_ok, '可走' if n_ok else '碰撞'))
RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
print('DONE')
