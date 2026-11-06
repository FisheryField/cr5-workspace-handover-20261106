# -*- coding: utf-8 -*-
"""轨迹11 新工作点可行性（位姿级）：
变换：非转运点 y+203、全部 z+170（与轨迹12 同规则）；转运点 y 不动。
判定：链式多种子 IK → 实机限位 → FK 回代 → Collisions() 全清（圆柱/挡板/安装台/地面）。
不改站内场景；全过则臂停工作点1 并截图。"""
import sys, io, os, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import *
from robodk.robomath import *

JSON_PATH = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹11.json'
DY, DZ = 203.0, 170.0
LIM = (180.0, 180.0, 160.0, 190.0, 180.0, 360.0)
SEEDS = ([0.0] * 6, [75.8, 106.1, -81.8, -24.3, -75.8, 0.0], [-75.8, -106.1, 81.8, 24.3, 75.8, 0.0],
         [30.0] * 6, [-30.0] * 6, [90.0, -30.0, -60.0, 0.0, 90.0, 0.0],
         [-90.0, -30.0, -60.0, 0.0, -90.0, 0.0])

with open(JSON_PATH, 'r', encoding='utf-8') as f:
    TRAJ = [p['values'] for p in json.load(f)]
print('轨迹11 点数 = %d' % len(TRAJ))

RDK = Robolink()
ORIG_RUNMODE = RDK.RunMode()
RDK.setRunMode(RUNMODE_SIMULATE)
robot = RDK.Item('', ITEM_TYPE_ROBOT)
cyl = RDK.Item('磨砂圆柱_R150_H50', ITEM_TYPE_OBJECT)
baffle = RDK.Item('挡板_半封闭3面', ITEM_TYPE_OBJECT)
table = RDK.Item('安装台_650x650x80mm', ITEM_TYPE_OBJECT)
ground = RDK.Item('地面_禁止穿越', ITEM_TYPE_OBJECT)
handle = RDK.Item('门把手_bs1')

print('场景核对：圆柱 y=%.1f z=%.1f  挡板 y=%.1f z=%.1f' % (
    cyl.Pose()[1, 3], cyl.Pose()[2, 3], baffle.Pose()[1, 3], baffle.Pose()[2, 3]))
pt = Pose_2_Fanuc(robot.PoseTool())
if abs(pt[2] - 100.0) > 1e-6:
    print('!! PoseTool 被清零，恢复 [0,0,100]')
    robot.setPoseTool(Pose(0, 0, 100, 0, 0, 0))

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

fails = []
prev = [0.0] * 6
first_ok_ql = None
for idx, (x, y, z, rx, ry, rz) in enumerate(TRAJ):
    if abs(y) > 1e-9:                       # 工作点：随图案平移
        tgt = (x, y + DY, z + DZ, rx, ry, rz)
        tag = '工作点%d' % idx
    else:                                   # 转运点：只抬 z
        tgt = (x, y, z + DZ, rx, ry, rz)
        tag = '转运点%d' % idx
    ql, err = solve_point(tgt, prev)
    if ql is None:
        print('X  %-6s TCP=(%.0f,%.0f,%.0f,%g,%g,%g)  %s' % (tag, tgt[0], tgt[1], tgt[2], tgt[3], tgt[4], tgt[5], err))
        fails.append((idx, tgt, err))
    else:
        print('OK %-6s TCP=(%.0f,%.0f,%.0f,%g,%g,%g)  q=[%s]' % (
            tag, tgt[0], tgt[1], tgt[2], tgt[3], tgt[4], tgt[5],
            ', '.join('%.1f' % v for v in ql)))
        prev = ql
        if first_ok_ql is None and tag == '工作点1':
            first_ok_ql = ql

if not fails:
    print('=== 轨迹11 全 %d 点通过（工作点(0,-572,470)）===' % len(TRAJ))
    if first_ok_ql:
        robot.setJoints(first_ok_ql)
        RDK.Render(True)
        time.sleep(2.0)
        SHOT = r'D:\mydata\glm-workplace\tools\rdk_traj11_new.png'
        if os.path.exists(SHOT): os.remove(SHOT)
        r = RDK.Cam2D_Snapshot(SHOT, None)
        print('工作点1位形截图 ret=%r size=%d' % (r, os.path.getsize(SHOT) if os.path.exists(SHOT) else -1))
else:
    print('=== 失败 %d 点（详见上表）===' % len(fails))
    robot.setJoints([0.0] * 6)

RDK.setRunMode(ORIG_RUNMODE)
print('RunMode -> %r；场景未改动；未保存工作站' % ORIG_RUNMODE)
