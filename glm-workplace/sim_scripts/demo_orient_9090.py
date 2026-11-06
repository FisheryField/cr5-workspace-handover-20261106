# -*- coding: utf-8 -*-
"""验证 [90,0,90] 姿态：①红框面法向在世界系的朝向；②若要面压滚轮顶/底 crown 线，
TCP 需在哪、IK 是否可达。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose, invH

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_head', 'exec'), ns)
from_fanuc = ns['fanuc_values_to_pose']

R = from_fanuc(0, 0, 0, 90.0, 0.0, 90.0)
def col(j):
    return tuple(round(R[i, j], 4) for i in range(3))
print('[90,0,90] 工具轴世界像：x̂=%s ŷ=%s ẑ=%s' % (col(0), col(1), col(2)))
# 红框面法向 ±ŷ_tool → 世界
ny_up = col(1)
print('红框面法向 +Y_tool → 世界 %s ; -Y_tool → %s' % (ny_up, tuple(-v for v in ny_up)))

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)

def ik_test(name, x, y, z):
    T = Fanuc_2_Pose([x, y, z, 90.0, 0.0, 90.0])
    fl = robot.PoseFrame() * T * invH(robot.PoseTool())
    s = robot.SolveIK_All(fl).tolist()
    if s and isinstance(s[0], (int, float)):
        s = [s]
    print('%s -> %s' % (name, '%d 解' % len(s) if s else '无解'))
    return len(s) > 0

# 滚轮：轴∥X, 中心 y=-922, 顶冠 z=610, 底冠 z=330（面法向朝外=∓Z）
print()
ik_test('顶冠贴合 TCP=(0,-922,622.3,90,0,90)', 0.0, -922.0, 622.3)
ik_test('底冠贴合 TCP=(0,-922,317.7,90,0,90)', 0.0, -922.0, 317.7)
ik_test('对照 P19 位 (35,-699,380,90,0,90)', 35.0, -699.0, 380.0)
print('DONE')
