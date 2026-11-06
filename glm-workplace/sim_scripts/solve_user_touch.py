# -*- coding: utf-8 -*-
"""读取用户手动摆的贴合位姿 → FK 得 TCP → 沿 +Y（离滚轮方向）逐步微退，
找到最近的无碰撞工作点，输出坐标与关节。"""
import sys, io, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import invH

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_head', 'exec'), ns)
to_fanuc = ns['pose_to_fanuc_values']
traj = ns['_trajectory_pose']

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)

q0 = [float(v) for v in robot.Joints().list()[:6]]
print('当前模型关节 =', ['%.3f' % v for v in q0])
tcp = [float(v) for v in to_fanuc(traj(q0))[:6]]
print('当前 TCP(Fanuc) = (%.3f, %.3f, %.3f, %.3f, %.3f, %.3f)' % tuple(tcp))

RDK.setRunMode(robolink.RUNMODE_SIMULATE)
robot.setJoints(q0)
hit0 = robot.MoveJ_Test(q0, q0, minstep_deg=1) != 0
print('当前位姿碰撞 =', '是' if hit0 else '否')

if not hit0:
    print('本来就无碰撞——直接用当前坐标。')
    RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
    raise SystemExit

# 沿 +Y 微退（每步 0.2mm，最多 20mm），保持姿态与 x/z 不变，重解 IK
found = None
for step in range(1, 101):
    dy = 0.2 * step
    y_new = tcp[1] + dy
    T = ns['fanuc_values_to_pose'](tcp[0], y_new, tcp[2], tcp[3], tcp[4], tcp[5])
    fl = robot.PoseFrame() * T * invH(robot.PoseTool())
    s = robot.SolveIK_All(fl).tolist()
    if s and isinstance(s[0], (int, float)):
        s = [s]
    if not s:
        continue
    # 取离当前关节最近的解
    q = [float(v) for v in min(s, key=lambda sol: sum((float(sol[j]) - q0[j]) ** 2 for j in range(6)))[:6]]
    if robot.MoveJ_Test(q, q, minstep_deg=1) == 0:
        found = (y_new, dy, q)
        break
    if step % 10 == 0:
        print('  退 %.1fmm 仍碰撞…' % dy)

if found:
    y_new, dy, q = found
    print('\n=== 最近无碰撞工作点 ===')
    print('  相对当前位沿 +Y 退了 %.1fmm' % dy)
    print('  TCP = (%.3f, %.3f, %.3f, %.3f, %.3f, %.3f)' % (
        tcp[0], y_new, tcp[2], tcp[3], tcp[4], tcp[5]))
    print('  关节 =', ['%.3f' % v for v in q])
    print('  碰撞检查 = 无碰撞')
else:
    print('\n+Y 退 20mm 内无解——冲突可能不在 Y 向（检查姿态/其它部件）')

RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
print('DONE（runmode 已复位；模型关节未改，保持你摆的样子）')
