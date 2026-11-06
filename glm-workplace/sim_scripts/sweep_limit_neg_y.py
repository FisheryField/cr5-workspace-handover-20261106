# -*- coding: utf-8 -*-
"""保持用户倾斜姿态 (rx,ry,rz)=(-88.938,-59.662,-90.931)，x/z 不变，
沿 -Y 从浅到深 0.25mm 步进扫描，标出清/撞边界，取碰撞前最深的清白位并摆模型。"""
import sys, io, os
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

Q_REF = [56.538, 99.350, -40.827, -57.550, 33.452, -60.478]   # 参考（清白位关节）

def test(y):
    T = from_fanuc(-1.163, y, 382.666, -88.938, -59.662, -90.931)
    fl = robot.PoseFrame() * T * invH(robot.PoseTool())
    s = robot.SolveIK_All(fl).tolist()
    if s and isinstance(s[0], (int, float)):
        s = [s]
    if not s:
        return None, None
    q = [float(v) for v in min(s, key=lambda sol: sum((float(sol[j]) - Q_REF[j]) ** 2 for j in range(6)))[:6]]
    hit = robot.MoveJ_Test(q, q, minstep_deg=1) != 0
    return q, hit

print('y         状态')
last_clear = None
y = -680.0
while y >= -712.0:
    q, hit = test(y)
    if q is None:
        print('%8.2f  无解' % y)
    else:
        print('%8.2f  %s' % (y, '碰撞' if hit else '清白'))
        if not hit:
            last_clear = (y, q)
        elif last_clear is not None and last_clear[0] > y > y - 0.3:
            break   # 刚从清白跨入碰撞
    y -= 0.25

if last_clear:
    y_lim, q = last_clear
    print('\n=== 碰撞前极限位（该姿态下 -Y 最深清白点）===')
    print('  TCP = (-1.163, %.3f, 382.666, -88.938, -59.662, -90.931)' % y_lim)
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
    print('模型已停在极限位（SIMULATE）。')
print('DONE')
