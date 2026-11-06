# -*- coding: utf-8 -*-
"""诊断用户贴合位碰撞：①报碰撞副；②+Y 加大退距扫描；③把姿态掰正(ry=-90)对照。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose, invH

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_head', 'exec'), ns)
to_fanuc = ns['pose_to_fanuc_values']
from_fanuc = ns['fanuc_values_to_pose']
traj = ns['_trajectory_pose']

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
Q_USER = [57.550, 94.750, -30.020, -63.730, 32.440, -60.510]

RDK.setRunMode(robolink.RUNMODE_SIMULATE)
robot.setJoints(Q_USER)
r = robot.MoveJ_Test(Q_USER, Q_USER, minstep_deg=1)
print('用户位姿碰撞 =', r != 0)
try:
    print('碰撞副 =', RDK.CollisionPairs() and '；'.join(
        '%s vs %s' % (a.Name(), b.Name()) for a, b in RDK.CollisionPairs()) or '（空）')
except Exception as e:
    print('CollisionPairs EXC:', e)

def test_tcp(name, x, y, z, rx, ry, rz):
    T = from_fanuc(x, y, z, rx, ry, rz)
    fl = robot.PoseFrame() * T * invH(robot.PoseTool())
    s = robot.SolveIK_All(fl).tolist()
    if s and isinstance(s[0], (int, float)):
        s = [s]
    if not s:
        print('%s -> 无解' % name)
        return
    q = [float(v) for v in min(s, key=lambda sol: sum((float(sol[j]) - Q_USER[j]) ** 2 for j in range(6)))[:6]]
    hit = robot.MoveJ_Test(q, q, minstep_deg=1) != 0
    print('%s -> %s' % (name, '碰撞' if hit else '无碰撞'))

# +Y 大退距（保持用户姿态）
for dy in (30, 40, 60):
    test_tcp('用户姿态 退%+dmm' % dy, -1.163, -708.953 + dy, 382.666, -88.938, -59.662, -90.931)
# 掰正姿态（ry=-90, 用用户 xz 深度）在不同深度
for y in (-707.2, -708.0, -709.0):
    test_tcp('姿态掰正 y=%.1f' % y, 0.0, y, 380.0, 0.0, -90.0, 180.0)
RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
print('DONE')
