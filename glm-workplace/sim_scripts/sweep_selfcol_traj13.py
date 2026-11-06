# -*- coding: utf-8 -*-
"""自干涉校准 + 轨迹13 全点重扫（找出离臂更远的自碰干净工作点区间）。

校准：
  A) 实机自干涉报警时的实际关节（15:16:43 日志）→ 期望 RoboDK 自碰 >0
  B) 上午 25/25 跑通的 P25 关节 → 期望 RoboDK 自碰 =0
自碰对：robot×robot 连杆 (i,j), |i-j|≥2；门把手×连杆1-4。外部四障碍对保持。
扫描：Δ∈[56,350] 步10 → 轨迹13 全19点，记录每档 自碰/外碰/限位 与 J4、J5 折叠度。"""
import sys, io, os, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import *
from robodk.robomath import *

JSON_PATH = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹13.json'
LIM = (180.0, 180.0, 160.0, 190.0, 180.0, 360.0)
SEEDS = ([0.0] * 6, [75.8, 106.1, -81.8, -24.3, -75.8, 0.0], [-75.8, -106.1, 81.8, 24.3, 75.8, 0.0],
         [30.0] * 6, [-30.0] * 6, [90.0, -30.0, -60.0, 0.0, 90.0, 0.0],
         [-90.0, -30.0, -60.0, 0.0, -90.0, 0.0])

# 轨迹13 是 Δ=+203 版；扫描时用原始轨迹7/11 思路 —— 直接以轨迹11 原始值 + Δ 参数化
SRC11 = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹11.json'
with open(SRC11, 'r', encoding='utf-8') as f:
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
    print('!! PoseTool 清零，恢复 [0,0,100]')
    robot.setPoseTool(Pose(0, 0, 100, 0, 0, 0))

# ---- 碰撞对：外部 + 自碰 ----
def enable_all_pairs():
    for obst in (cyl, baffle, table, ground):
        for link in range(1, 7):
            RDK.setCollisionActivePair(COLLISION_ON, robot, obst, link, 0)
        if handle.Valid():
            RDK.setCollisionActivePair(COLLISION_ON, handle, obst)
    RDK.setCollisionActivePair(COLLISION_OFF, robot, table, 0, 0)
    n_self = 0
    for i in range(1, 7):
        for j in range(i + 2, 7):          # 非相邻连杆自碰
            if RDK.setCollisionActivePair(COLLISION_ON, robot, robot, i, j) == 1:
                n_self += 1
    if handle.Valid():
        for link in range(1, 5):           # 把手 × 近端连杆
            RDK.setCollisionActivePair(COLLISION_ON, handle, robot, link, 0)
    RDK.setCollisionActive(COLLISION_ON)
    return n_self

print('自碰对启用数 =', enable_all_pairs())

def place_unit(delta):
    """圆柱/挡板一体：圆柱 y_c = -916+Δ，挡板 y = 0+Δ（相对原位同幅）。"""
    P = cyl.Pose(); P[1, 3] = -916.0 + delta; cyl.setPose(P)
    B = baffle.Pose(); B[1, 3] = delta; baffle.setPose(B)

def check_collisions():
    n = RDK.Collisions() or 0
    if n == 0:
        return 0, None
    names = ','.join(sorted({i.Name() for i in RDK.CollisionItems()}))
    return n, names

# ---- 校准 ----
print('--- 校准 ---')
robot.setJoints([41.58025655746462, 61.050722275484226, -89.39285585384613, -151.65786973382683, 41.58025655746462, -180.0])
n, names = check_collisions()
print('A) P3 实机自干涉位形 [41.58,61.05,-89.39,-151.66,41.58,-180] → 碰撞数=%s 对=%s（期望>0）' % (n, names))
robot.setJoints([-13.591622773947876, 90.16498150511222, -83.69963752064464, 83.53465601553239, -90.0, 166.40837722605215])
n2, names2 = check_collisions()
print('B) P25 跑通位形 [-13.59,90.16,-83.70,83.53,-90,166.41] → 碰撞数=%s 对=%s（期望=0）' % (n2, names2))

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
        return None, 'IK/限位'
    robot.setJoints(best)
    n, names = check_collisions()
    if n:
        return None, '碰撞:' + (names or '?')
    return best, None

# ---- 扫描 ----
print('--- Δ扫描（轨迹13 全19点，含自碰判定）---')
results = []
for delta in range(56, 351, 10):
    place_unit(delta)
    prev = [0.0] * 6
    fail = None
    max_j4 = 0.0
    min_j5_margin = 999.0
    for idx, (x, y, z, rx, ry, rz) in enumerate(TRAJ):
        if abs(y) > 1e-9:
            tgt = (x, y + delta, z + 170.0, rx, ry, rz)   # 相对原始轨迹11 平移
        else:
            tgt = (x, y, z + 170.0, rx, ry, rz)
        ql, err = solve_point(tgt, prev)
        if ql is None:
            fail = (idx, err)
            break
        prev = ql
        max_j4 = max(max_j4, abs(ql[3]))
        min_j5_margin = min(min_j5_margin, 180.0 - abs(ql[4]))
    ok = fail is None
    lineA = -775.0 + delta
    results.append((delta, lineA, ok, fail, max_j4, min_j5_margin))
    if ok:
        print('OK Δ=%+4d 线A=%7.1f  max|J4|=%6.1f  J5距±180=%6.1f' % (delta, lineA, max_j4, min_j5_margin))
    else:
        print('X  Δ=%+4d 线A=%7.1f  失败点%d %s' % (delta, lineA, fail[0], fail[1]))

clean = [r for r in results if r[2]]
print('=== 全清（外碰+自碰+限位）区间 ===')
if clean:
    ds = [r[0] for r in clean]
    a = b = ds[0]
    segs = []
    for d in ds[1:]:
        if d - b <= 11:
            b = d
        else:
            segs.append((a, b)); a = b = d
    segs.append((a, b))
    for a, b in segs:
        print('  Δ∈[%+d,%+d] → 线A∈[%.0f,%.0f] 圆柱y_c∈[%.0f,%.0f]' % (
            a, b, -775 + a, -775 + b, -916 + a, -916 + b))
    # 折叠度参考：干净档里的 max|J4| / J5 余量
    print('  干净档折叠度：max|J4| 最大 %.1f，J5 余量最小 %.1f' % (
        max(r[4] for r in clean), min(r[5] for r in clean)))
else:
    print('  （无全清档）')

# 场景恢复到扫描前（Δ=+203）
place_unit(203.0)
robot.setJoints([0.0] * 6)
RDK.setRunMode(ORIG_RUNMODE)
print('已恢复场景 Δ=+203（圆柱-713/挡板213），RunMode=%r' % ORIG_RUNMODE)
