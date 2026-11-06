# -*- coding: utf-8 -*-
"""轨迹7 中点方案落位验证：
线A=-572（可行域[-719,-425]中点），线B=-559，圆柱 R140 面=-573 → y_c=-713，z=470。
逐点：链式多种子IK → 实机限位 → FK回代 → Collisions() 全清。
全过则臂停在工作点1压紧位姿并截图；圆柱留在 -713。"""
import sys, io, os, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import *
from robodk.robomath import *

JSON_PATH = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹7.json'
DELTA = 203.0          # 线A: -775+203 = -572
CYL_Y = -713.0         # = -916+203
LIM = (180.0, 180.0, 160.0, 190.0, 180.0, 360.0)
SEEDS = ([0.0] * 6, [75.8, 106.1, -81.8, -24.3, -75.8, 0.0], [-75.8, -106.1, 81.8, 24.3, 75.8, 0.0],
         [30.0] * 6, [-30.0] * 6, [90.0, -30.0, -60.0, 0.0, 90.0, 0.0])

with open(JSON_PATH, 'r', encoding='utf-8') as f:
    TRAJ = [p['values'] for p in json.load(f)]

RDK = Robolink()
ORIG_RUNMODE = RDK.RunMode()
RDK.setRunMode(RUNMODE_SIMULATE)
robot = RDK.Item('', ITEM_TYPE_ROBOT)
cyl = RDK.Item('磨砂圆柱_R150_H50', ITEM_TYPE_OBJECT)
baffle = RDK.Item('挡板_半封闭3面', ITEM_TYPE_OBJECT)
table = RDK.Item('安装台_650x650x80mm', ITEM_TYPE_OBJECT)
ground = RDK.Item('地面_禁止穿越', ITEM_TYPE_OBJECT)
handle = RDK.Item('门把手_bs1')

pt = Pose_2_Fanuc(robot.PoseTool())
if abs(pt[2] - 100.0) > 1e-6:
    print('!! PoseTool 被清零，恢复 [0,0,100]')
    robot.setPoseTool(Pose(0, 0, 100, 0, 0, 0))

P = cyl.Pose(); P[1, 3] = CYL_Y; cyl.setPose(P)
print('圆柱已置于 (0, %.1f, 470) R140 面=-573' % CYL_Y)

# 挡板与圆柱一体：按原相对位置同幅平移（圆柱 Δy = -713-(-926) = +213；挡板 y 0→213）
baf = baffle
BP = baf.Pose(); BP[1, 3] = 213.0; baf.setPose(BP)
BP = baf.Pose()
print('挡板已同幅平移 -> t=(%.1f, %.1f, %.1f)（原相对位置保持：挡板前缘过圆柱轴心）' % (
    BP[0, 3], BP[1, 3], BP[2, 3]))

for obst in (cyl, baffle, table, ground):
    for link in range(1, 7):
        RDK.setCollisionActivePair(COLLISION_ON, robot, obst, link, 0)
    if handle.Valid():
        RDK.setCollisionActivePair(COLLISION_ON, handle, obst)
RDK.setCollisionActivePair(COLLISION_OFF, robot, table, 0, 0)
RDK.setCollisionActive(COLLISION_ON)

def in_limits(ql):
    return all(abs(v) <= L + 1e-6 for v, L in zip(ql, LIM))

def solve_point(fanuc, prev):
    pose = Fanuc_2_Pose(fanuc)
    fl = pose * invH(robot.PoseTool())
    cands = []
    for seed in (([prev] if prev is not None else []) + list(SEEDS)):
        q = robot.SolveIK(fl, seed)
        if q is not None:
            cands.append(list(q.list()[:6]))
    for col in (robot.SolveIK_All(fl) or []):
        cands.append([float(v) for v in list(col)[:6]])
    best, best_cost = None, 1e18
    for ql in cands:
        tcp = robot.SolveFK(ql) * robot.PoseTool()
        err = max(abs(tcp[a, b] - pose[a, b]) for a in range(4) for b in range(4))
        if err > 1e-3 or not in_limits(ql):
            continue
        cost = sum(abs(a - b) for a, b in zip(ql, prev)) if prev is not None else 0.0
        if cost < best_cost:
            best, best_cost = ql, cost
    if best is None:
        return None, 'IK/限位失败'
    robot.setJoints(best)
    if (RDK.Collisions() or 0) > 0:
        names = ','.join(sorted({i.Name() for i in RDK.CollisionItems()}))
        return None, '碰撞:' + names
    return best, None

fail = None
prev = [0.0] * 6
solutions = []
for idx, (x, y, z, rx, ry, rz) in enumerate(TRAJ):
    if 1 <= idx <= 8:
        tgt = (x, y + DELTA, z + 170.0, rx, ry, rz)
    else:
        tgt = (x, y, z + 170.0, rx, ry, rz)
    ql, err = solve_point(tgt, prev)
    tag = '工作点%d' % idx if 1 <= idx <= 8 else '转运点%d' % idx
    if ql is None:
        print('X  %-6s TCP=(%.0f,%.0f,%.0f,%g,%g,%g)  %s' % (tag, tgt[0], tgt[1], tgt[2], tgt[3], tgt[4], tgt[5], err))
        fail = (idx, err)
        solutions.append(None)
    else:
        print('OK %-6s TCP=(%.0f,%.0f,%.0f,%g,%g,%g)  q=[%s]' % (
            tag, tgt[0], tgt[1], tgt[2], tgt[3], tgt[4], tgt[5],
            ', '.join('%.1f' % v for v in ql)))
        prev = ql
        solutions.append(ql)

if fail is None:
    print('=== 轨迹7 全10点通过（Δ=+203，线A=-572，圆柱 y=-713）===')
    robot.setJoints(solutions[1])       # 停在工作点1压紧位姿
    RDK.Render(True)
    time.sleep(2.0)
    SHOT = r'D:\mydata\glm-workplace\tools\rdk_traj7_mid.png'
    if os.path.exists(SHOT): os.remove(SHOT)
    r = RDK.Cam2D_Snapshot(SHOT, None)
    print('工作点1位形截图 ret=%r size=%d' % (r, os.path.getsize(SHOT) if os.path.exists(SHOT) else -1))
else:
    print('=== 有失败点（工作点%d: %s）===' % (fail[0], fail[1]))
    robot.setJoints([0.0] * 6)

RDK.setRunMode(ORIG_RUNMODE)
print('RunMode 恢复尝试 -> %r（当前 %r）；圆柱留在 y=-713；未保存工作站' % (ORIG_RUNMODE, RDK.RunMode()))
