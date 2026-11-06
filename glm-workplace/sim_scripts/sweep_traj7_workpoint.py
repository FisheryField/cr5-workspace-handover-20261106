# -*- coding: utf-8 -*-
"""轨迹7 全位姿可行性扫描（仅仿真；finally 恢复关节/RunMode；圆柱恢复 y=-915）。

参数化：Δ = 工作图案沿 y 的整体平移。
  工作点 i(1..8): (x_i, y_i+Δ, z_i+170) —— z 随场景+170，间隙结构保持
  转运点 0/9:     (±500, 0, 470)
  圆柱: y_c = -916+Δ（面 = y_c+140 = -776+Δ；工作线A = 面+1 = -775+Δ，线B = 面+14）
判定：链式 IK（前点解作种子）→ FK 回代 <1e-3 → 实机限位 (180,180,160,190,180,360)
      → setJoints → 机器人/门把手 对 圆柱/挡板/安装台/地面 碰撞全0。
"""
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import *
from robodk.robomath import *

JSON_PATH = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹7.json'
LIM = (180.0, 180.0, 160.0, 190.0, 180.0, 360.0)
WORK_IDX = range(1, 9)          # 工作点
TRANSIT_IDX = (0, 9)            # 转运点

with open(JSON_PATH, 'r', encoding='utf-8') as f:
    TRAJ = [p['values'] for p in json.load(f)]
print('轨迹7 点数 = %d' % len(TRAJ))

RDK = Robolink()
ORIG_RUNMODE = RDK.RunMode()
if RDK.RunMode() != RUNMODE_SIMULATE:
    RDK.setRunMode(RUNMODE_SIMULATE)
robot = RDK.Item('', ITEM_TYPE_ROBOT)
q0m = robot.Joints()
cyl = RDK.Item('磨砂圆柱_R150_H50', ITEM_TYPE_OBJECT)
baffle = RDK.Item('挡板_半封闭3面', ITEM_TYPE_OBJECT)
table = RDK.Item('安装台_650x650x80mm', ITEM_TYPE_OBJECT)
ground = RDK.Item('地面_禁止穿越', ITEM_TYPE_OBJECT)
handle = RDK.Item('门把手_bs1')
OBSTS = [cyl, baffle, table, ground]

# PoseTool 守护（连接同步可能清零，v14w17 僵尸）
pt = Pose_2_Fanuc(robot.PoseTool())
if abs(pt[2] - 100.0) > 1e-6:
    print('!! PoseTool 被清零（%s），恢复 [0,0,100]' % ['%.1f' % v for v in pt])
    robot.setPoseTool(Pose(0, 0, 100, 0, 0, 0))

for obst in OBSTS:
    for link in range(1, 7):          # 镜像宏：link0(基座)不参与，基座本就坐在安装台上
        RDK.setCollisionActivePair(COLLISION_ON, robot, obst, link, 0)
    if handle.Valid():
        RDK.setCollisionActivePair(COLLISION_ON, handle, obst)
# 显式关掉可能残留的 link0×安装台（配对跨脚本持久；第一遍误开过）
RDK.setCollisionActivePair(COLLISION_OFF, robot, table, 0, 0)
RDK.setCollisionActive(COLLISION_ON)

def place_cyl(delta):
    P = cyl.Pose(); P[1, 3] = -916.0 + delta; cyl.setPose(P)

def in_limits(ql):
    return all(abs(v) <= L + 1e-6 for v, L in zip(ql, LIM))

SEEDS = ([0.0] * 6, [75.8, 106.1, -81.8, -24.3, -75.8, 0.0], [-75.8, -106.1, 81.8, 24.3, 75.8, 0.0],
         [30.0] * 6, [-30.0] * 6, [90.0, -30.0, -60.0, 0.0, 90.0, 0.0])

def solve_point(fanuc, prev):
    """返回 (关节list, 原因)；prev=None 表示无种子。fanuc 为 TCP 目标。"""
    pose = Fanuc_2_Pose(fanuc)
    fl = pose * invH(robot.PoseTool())       # SolveIK/All 解的是法兰
    cands = []
    for seed in (([prev] if prev is not None else []) + list(SEEDS)):
        q = robot.SolveIK(fl, seed)
        if q is not None:
            cands.append(list(q.list()[:6]))
    qa = robot.SolveIK_All(fl)
    for col in (qa or []):
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
    # Item.Collision 是裸检（基座贴装=恒撞）；Collisions()/CollisionItems() 才尊重碰撞对配置
    if (RDK.Collisions() or 0) > 0:
        names = ','.join(sorted({i.Name() for i in RDK.CollisionItems()}))
        return None, '碰撞:' + names
    return best, None

def eval_delta(delta):
    place_cyl(delta)
    prev = [0.0] * 6
    fail_work = fail_transit = None
    for idx in range(len(TRAJ)):
        x, y, z, rx, ry, rz = TRAJ[idx]
        if idx in WORK_IDX:
            tgt = (x, y + delta, z + 170.0, rx, ry, rz)
        else:
            tgt = (x, y, z + 170.0, rx, ry, rz)
        ql, err = solve_point(tgt, prev)
        if ql is None:
            if idx in WORK_IDX and fail_work is None:
                fail_work = (idx, tgt, err)
            if idx in TRANSIT_IDX and fail_transit is None:
                fail_transit = (idx, tgt, err)
            # 链断了：后续以失败点前的 prev 继续尝试（只统计，不中断整条）
            continue
        prev = ql
    return fail_work, fail_transit

try:
    # 重点区间：边界加密 Δ=45..65 逐1；上界延伸到 +550（步10）；保留 -190..+50 抽档复核
    deltas = sorted(set(list(range(-190, 51, 30)) + list(range(45, 66)) + list(range(70, 551, 10)) + [1]))
    feasible = []
    print('Δ扫描：%d 档（工作点 y = -775+Δ，圆柱 y_c = -916+Δ）' % len(deltas))
    for d in deltas:
        fw, ft = eval_delta(d)
        ok = (fw is None)
        mark = 'OK ' if ok else 'X  '
        extra = ''
        if fw: extra += ' 工作点%d@(%g,%g,%g,%g,%g,%g) %s' % ((fw[0],) + fw[1] + (fw[2],))
        if ft: extra += ' | 转运点%d %s' % (ft[0], ft[2])
        print('%s Δ=%+4d 工作线A y=%7.1f 圆柱 y_c=%7.1f%s' % (mark, d, -775 + d, -916 + d, extra))
        if ok:
            feasible.append(d)
    # 连续区间
    intervals = []
    if feasible:
        a = b = feasible[0]
        for d in feasible[1:]:
            if d == b + 10 or d == b + 1 or (d - b) <= 11:
                b = d
            else:
                intervals.append((a, b)); a = b = d
        intervals.append((a, b))
    print('=== 可行 Δ 区间（步距≤11 合并）===')
    for a, b in intervals:
        print('  Δ ∈ [%+d, %+d]  →  工作线A y ∈ [%.0f, %.0f]  圆柱 y_c ∈ [%.0f, %.0f]' % (
            a, b, -775 + a, -775 + b, -916 + a, -916 + b))
    if not intervals:
        print('  （粗扫无完整可行档，需放宽判定或细扫）')
finally:
    robot.setJoints(q0m)
    P = cyl.Pose(); P[1, 3] = -915.0; cyl.setPose(P)   # 圆柱恢复到第一步结果
    RDK.setRunMode(ORIG_RUNMODE)
    print('已恢复：关节=%s 圆柱 y=-915 RunMode=%r' % (
        ['%.1f' % v for v in robot.Joints().list()[:6]], RDK.RunMode()))
