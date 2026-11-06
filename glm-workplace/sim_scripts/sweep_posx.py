# -*- coding: utf-8 -*-
"""从当前极限位 TCP=(-1.163,-685,382.666,-88.938,-59.662,-90.931) 出发，
x 沿 +X 以 2mm 步进扫到 +120，保持 y/z/姿态，逐点 IK+碰撞检测。"""
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
RDK.setRunMode(robolink.RUNMODE_SIMULATE)

Q_REF = [56.540, 99.342, -40.809, -57.560, 33.450, -60.478]
Y, Z = -685.000, 382.666
RX, RY, RZ = -88.938, -59.662, -90.931

print('x        状态')
transitions = []
prev = None
x = -1.163
while x <= 120.5:
    T = from_fanuc(x, Y, Z, RX, RY, RZ)
    fl = robot.PoseFrame() * T * invH(robot.PoseTool())
    s = robot.SolveIK_All(fl).tolist()
    if s and isinstance(s[0], (int, float)):
        s = [s]
    if not s:
        st = '无解'
        q = None
    else:
        q = [float(v) for v in min(s, key=lambda sol: sum((float(sol[j]) - Q_REF[j]) ** 2 for j in range(6)))[:6]]
        hit = robot.MoveJ_Test(q, q, minstep_deg=1) != 0
        st = '碰撞' if hit else '清白'
    print('%7.1f  %s' % (x, st))
    if prev is not None and st != prev:
        transitions.append((x, prev, st))
    prev = st
    x += 2.0

print('\n状态切换点：')
for x, a, b in transitions:
    print('  x=%.1f : %s → %s' % (x, a, b))
if not transitions:
    print('  （全程无切换，一直是「%s」）' % prev)
RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
print('DONE')
