# -*- coding: utf-8 -*-
"""压缩把手模型下，P23/P25 倾斜姿态在 (30, y, 460) 的净空边界扫描。"""
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
ns['_ensure_canonical_tool']()

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
RDK.setRunMode(robolink.RUNMODE_SIMULATE)

def clear(y, ry):
    T = from_fanuc(30.0, y, 460.0, -88.932, ry, -90.936)
    fl = robot.PoseFrame() * T * invH(robot.PoseTool())
    s = robot.SolveIK_All(fl).tolist()
    if s and isinstance(s[0], (int, float)):
        s = [s]
    if not s:
        return None
    q = [float(v) for v in s[0][:6]]
    return robot.MoveJ_Test(q, q, minstep_deg=1) == 0

for ry, tag in ((-59.663, 'P23'), (59.663, 'P25')):
    deepest = None
    for y10 in range(-6500, -6901, -5):   # -650 → -690, 0.5mm步
        y = y10 / 10.0
        c = clear(y, ry)
        if c is None:
            break
        if c:
            deepest = y
        elif deepest is not None:
            break
    print('%s(ry=%+.3f) 最深无碰撞 y = %s' % (tag, ry, deepest))
RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
print('DONE')
