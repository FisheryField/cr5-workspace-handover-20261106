# -*- coding: utf-8 -*-
"""读当前模型状态（关节/TCP/PoseTool/碰撞）→ 若 PoseTool≠182 先纠正 →
仅沿 +Y 扫到首个无碰撞位并摆模型。"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose, invH

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_head', 'exec'), ns)
from_fanuc = ns['fanuc_values_to_pose']
to_fanuc = ns['pose_to_fanuc_values']
traj = ns['_trajectory_pose']

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)

t = robot.PoseTool().Pos()
print('PoseTool =', ['%.3f' % v for v in t])
if abs(t[0]) < 1e-9 and abs(t[1]) < 1e-9 and abs(abs(t[2]) - 182.0) > 1e-6:
    robot.setPoseTool(Fanuc_2_Pose([0.0, 0.0, 182.0, 0.0, 0.0, 0.0]))
    print('!! PoseTool 已被改坏——已恢复 [0,0,182]（碰撞判定必须用正确工具）')

q0 = [float(v) for v in robot.Joints().list()[:6]]
print('模型关节 =', ['%.3f' % v for v in q0])
tcp0 = [float(v) for v in to_fanuc(traj(q0))[:6]]
print('当前 TCP = (%.3f, %.3f, %.3f, %.3f, %.3f, %.3f)' % tuple(tcp0))

RDK.setRunMode(robolink.RUNMODE_SIMULATE)
hit0 = robot.MoveJ_Test(q0, q0, minstep_deg=1) != 0
print('当前碰撞 =', '是' if hit0 else '否')

if not hit0:
    print('本来就不碰撞——位置不动。')
    RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
    raise SystemExit

found = None
dy = 0.25
while dy <= 30.0:
    y = tcp0[1] + dy
    T = from_fanuc(tcp0[0], y, tcp0[2], tcp0[3], tcp0[4], tcp0[5])
    fl = robot.PoseFrame() * T * invH(robot.PoseTool())
    s = robot.SolveIK_All(fl).tolist()
    if s and isinstance(s[0], (int, float)):
        s = [s]
    if s:
        q = [float(v) for v in min(s, key=lambda sol: sum((float(sol[j]) - q0[j]) ** 2 for j in range(6)))[:6]]
        if robot.MoveJ_Test(q, q, minstep_deg=1) == 0:
            found = (dy, y, q)
            break
    dy += 0.25

if found:
    dy, y, q = found
    print('\n=== 首个无碰撞位（仅 +Y 移动 %.2fmm）===' % dy)
    print('  TCP = (%.3f, %.3f, %.3f, %.3f, %.3f, %.3f)' % (
        tcp0[0], y, tcp0[2], tcp0[3], tcp0[4], tcp0[5]))
    print('  关节 =', ['%.3f' % v for v in q])
    robot.setJoints(q)
    OUT = r'D:\mydata\glm-workplace\tools\contact_pose_demo.png'
    if os.path.exists(OUT):
        os.remove(OUT)
    try:
        RDK.Cam2D_Snapshot(OUT, None)
    except Exception:
        RDK.Cam2D_Snapshot(OUT, 0)
    print('截图 =', OUT if os.path.exists(OUT) else '失败')
else:
    print('+Y 30mm 内无解')
RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
print('DONE')
