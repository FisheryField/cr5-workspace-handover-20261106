# -*- coding: utf-8 -*-
"""J6 可调版贴合扫描：工具 ẑ→+X（P19 族），面法向随 J6 绕 ẑ 旋转扫过滚轮圆周。
对每个圆周角 φ（0=赤道向机器人为正前下方偏）构造贴合位姿并测 IK/碰撞，
找最靠近赤道的可达贴合点，摆位截图。"""
import sys, io, os, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose, Mat, invH

src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_head', 'exec'), ns)
to_fanuc = ns['pose_to_fanuc_values']

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)

YC, ZC, RAD, OFF = -922.0, 470.0, 150.0, 12.3

def contact_pose(phi_deg):
    """φ：圆周角，0=赤道最前点；正=上象限；负=下象限（朝机器人前下方）。"""
    p = math.radians(phi_deg)
    # 滚轮表面点（x=0 截面）与外法向
    W = (0.0, YC + RAD * math.cos(p), ZC + RAD * math.sin(p))
    n_roller = (0.0, math.cos(p), math.sin(p))          # 滚轮外法向
    n_face = tuple(-v for v in n_roller)                # 把手面外法向 = 压入方向
    # 工具 ẑ → +X；ŷ_tool → n_face；x̂ = ŷ×ẑ
    zw = (1.0, 0.0, 0.0)
    yw = n_face
    xw = (yw[1]*zw[2]-yw[2]*zw[1], yw[2]*zw[0]-yw[0]*zw[2], yw[0]*zw[1]-yw[1]*zw[0])
    m = Mat(4, 4)
    for i, ax in enumerate((xw, yw, zw)):
        for j in range(3):
            m[i, j] = ax[j]
    TCP = (W[0] + OFF * n_roller[0], W[1] + OFF * n_roller[1], W[2] + OFF * n_roller[2])
    m[0, 3], m[1, 3], m[2, 3] = TCP
    return m, TCP, W

print('φ(°)   TCP位置                  Fanuc[rx,ry,rz]        IK   碰撞')
reachable = []
for phi in range(0, -46, -5):
    m, TCP, W = contact_pose(phi)
    fan = [float(v) for v in to_fanuc(m)[:6]]
    fl = robot.PoseFrame() * m * invH(robot.PoseTool())
    s = robot.SolveIK_All(fl).tolist()
    if s and isinstance(s[0], (int, float)):
        s = [s]
    if not s:
        print('%+4d   (%7.1f,%8.1f,%6.1f)      [%6.1f,%5.1f,%5.1f]   无解' % (
            phi, TCP[0], TCP[1], TCP[2], fan[3], fan[4], fan[5]))
        continue
    q = [float(v) for v in s[0][:6]]
    reachable.append((phi, TCP, fan, q))
    print('%+4d   (%7.1f,%8.1f,%6.1f)      [%6.1f,%5.1f,%5.1f]   %d解  …' % (
        phi, TCP[0], TCP[1], TCP[2], fan[3], fan[4], fan[5], len(s)))

if not reachable:
    print('\n无任何可达贴合角。')
    raise SystemExit

# 选最靠近赤道的可达角（φ 最大）
phi, TCP, fan, q = reachable[0]
print('\n选定演示：φ=%+d°  TCP=(%.2f, %.2f, %.2f, %.2f, %.2f, %.2f)' % (
    phi, TCP[0], TCP[1], TCP[2], fan[3], fan[4], fan[5]))
RDK.setRunMode(robolink.RUNMODE_SIMULATE)
r = robot.MoveJ_Test(q, q, minstep_deg=1)
print('碰撞检查 =', '碰撞!' if r != 0 else '无碰撞')
if r != 0:
    # 退 0.5mm 再试
    m2, TCP2, _ = contact_pose(phi)
    m2[1, 3] += 0.5
    fl2 = robot.PoseFrame() * m2 * invH(robot.PoseTool())
    s2 = robot.SolveIK_All(fl2).tolist()
    if s2 and isinstance(s2[0], (int, float)):
        s2 = [s2]
    if s2:
        q = [float(v) for v in s2[0][:6]]
        r2 = robot.MoveJ_Test(q, q, minstep_deg=1)
        print('沿法向退 0.5mm 后碰撞 =', '碰撞!' if r2 != 0 else '无碰撞（贴面演示位）')
robot.setJoints(q)
OUT = r'D:\mydata\glm-workplace\tools\contact_pose_demo.png'
if os.path.exists(OUT):
    os.remove(OUT)
try:
    RDK.Cam2D_Snapshot(OUT, None)
except Exception:
    RDK.Cam2D_Snapshot(OUT, 0)
print('截图 =', OUT if os.path.exists(OUT) else '失败')
print('DONE（模型停在演示位，SIMULATE）')
