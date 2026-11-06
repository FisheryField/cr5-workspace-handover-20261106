# -*- coding: utf-8 -*-
"""逐个 J6 旋转角扫描：(20,y,380,[90,0,90]+J6Δ) 各角度的最深无碰撞 y。"""
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

def clear_at(y, d):
    T = fanuc_to_pose(20.0, y, 380.0, 90.0, 0.0, 90.0) * rotz(d)
    fl = robot.PoseFrame() * T * invH(robot.PoseTool())
    s = robot.SolveIK_All(fl).tolist()
    if s and isinstance(s[0], (int, float)):
        s = [s]
    if not s:
        return None
    q = [float(v) for v in s[0][:6]]
    return robot.MoveJ_Test(q, q, minstep_deg=1) == 0

for d in (0.0, 90.0, 180.0, 270.0):
    deepest = None
    hit_seen = False
    for y10 in range(-6000, -7101, -10):   # -600 → -710, 1mm 步
        y = y10 / 10.0
        c = clear_at(y, d)
        if c:
            deepest = y
        else:
            if deepest is not None:
                hit_seen = True
                break
    print('J6+%-4g° : 最深无碰撞 y = %s%s' % (d, deepest if deepest is not None else '（全段无清白）',
          '（继续加深即碰撞）' if hit_seen else '（扫到-710仍清白）'))
RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
print('DONE')
