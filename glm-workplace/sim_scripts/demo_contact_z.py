# -*- coding: utf-8 -*-
"""竖直姿态 y=-759.7 下 z 可达性扫描 + 摆位截图。"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose, invH

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)

def ik_ok(y, z):
    T = Fanuc_2_Pose([0.0, y, z, 180.0, 0.0, 0.0])
    fl = robot.PoseFrame() * T * invH(robot.PoseTool())
    s = robot.SolveIK_All(fl).tolist()
    if s and isinstance(s[0], (int, float)):
        s = [s]
    return len(s), (s[0][:6] if s else None)

print('竖直 (rx=180)  y=-759.7 扫 z：')
best = None
for z in range(380, 239, -10):
    n, sol = ik_ok(-759.7, float(z))
    print('  z=%d  %s' % (z, '有解(%d)' % n if n else '—'))
    if n and best is None:
        best = (z, sol)
print('最浅可达 z =', best[0] if best else None)

if best:
    z_show, sol = best
    # 取 z=280 优先（若可达），否则用扫描到的最浅可达
    n280, sol280 = ik_ok(-759.7, 280.0)
    if n280:
        z_show, sol = 280, sol280
    q = [float(v) for v in sol]
    print('演示位姿 TCP=(0,-759.7,%d,180,0,0) 关节=' % z_show, ['%.2f' % v for v in q])
    RDK.setRunMode(robolink.RUNMODE_SIMULATE)
    r = robot.MoveJ_Test(q, q, minstep_deg=1)
    print('碰撞检查 =', '碰撞!' if r != 0 else '无碰撞')
    robot.setJoints(q)
    OUT = r'D:\mydata\glm-workplace\tools\contact_pose_demo.png'
    if os.path.exists(OUT):
        os.remove(OUT)
    try:
        RDK.Cam2D_Snapshot(OUT, None)
    except Exception:
        RDK.Cam2D_Snapshot(OUT, 0)
    print('截图 =', OUT if os.path.exists(OUT) else '失败')
    print('模型已停在演示位姿（SIMULATE）。看完喊我复位。')
print('DONE')
