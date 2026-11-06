# -*- coding: utf-8 -*-
"""正确工具(182)下的真实可行性地图：关键点位 × J6 0/90/180/270，全分支清白判定。"""
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
fixed = ns['_ensure_canonical_tool']()
print('工具守护 =', '已恢复182' if fixed else '正常182')

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

pts = [(20.0, -700.0), (20.0, -707.0), (40.0, -694.0), (-20.0, -707.0), (35.0, -707.0)]
print('\n%-16s %-8s %-8s %-8s %-8s' % ('点位', 'J6+0', 'J6+90', 'J6+180', 'J6+270'))
for (x, y) in pts:
    row = []
    for d in (0.0, 90.0, 180.0, 270.0):
        n_sol, n_ok = any_clear(x, y, d)
        row.append('✓' if n_ok else '✗')
    print('(%5.1f,%7.1f)   %-8s %-8s %-8s %-8s' % (x, y, row[0], row[1], row[2], row[3]))
RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
print('\nDONE')
