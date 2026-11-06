# -*- coding: utf-8 -*-
"""健康分支扫描 + 落位 + 重生成轨迹13：
选解偏好 = |J4| 最小（对齐上午硬件接受族 J4∈[-3,-75]），同档内取离前点最近。
扫 Δ∈[56,166] 找全19点健康可解的档 → 取 Δ=+76（线A=-699）落位（圆柱/挡板一体），
重写 连续轨迹13.json（y+Δ、z+170），并输出健康关节表。"""
import sys, io, os, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import *
from robodk.robomath import *

SRC11 = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹11.json'
DST13 = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹13.json'
PICK_DELTA = 76.0
LIM = (180.0, 180.0, 160.0, 190.0, 180.0, 360.0)
SEEDS = ([0.0] * 6, [-70.0, -30.0, -60.0, -70.0, 70.0, -180.0], [-75.0, -27.0, -80.0, -72.0, -75.0, -180.0],
         [75.8, 106.1, -81.8, -24.3, -75.8, 0.0], [-75.8, -106.1, 81.8, 24.3, 75.8, 0.0],
         [30.0] * 6, [-30.0] * 6, [90.0, -30.0, -60.0, 0.0, 90.0, 0.0], [-90.0, -30.0, -60.0, 0.0, -90.0, 0.0],
         [-72.0, 4.0, -90.0, -4.0, 90.0, 18.0])

with open(SRC11, 'r', encoding='utf-8') as f:
    RAW = json.load(f)
TRAJ = [p['values'] for p in RAW]

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

for obst in (cyl, baffle, table, ground):
    for link in range(1, 7):
        RDK.setCollisionActivePair(COLLISION_ON, robot, obst, link, 0)
    if handle.Valid():
        RDK.setCollisionActivePair(COLLISION_ON, handle, obst)
RDK.setCollisionActivePair(COLLISION_OFF, robot, table, 0, 0)
RDK.setCollisionActive(COLLISION_ON)

def place_unit(delta):
    P = cyl.Pose(); P[1, 3] = -916.0 + delta; cyl.setPose(P)
    B = baffle.Pose(); B[1, 3] = delta; baffle.setPose(B)

def in_limits(ql):
    return all(abs(v) <= L + 1e-6 for v, L in zip(ql, LIM))

def solve_healthy(fanuc, prev):
    """健康选解：先收集全部 限位内+FK精确+无碰撞 候选；
    在 |J4| ≤ min|J4|+20 的档里取离 prev 最近。"""
    pose = Fanuc_2_Pose(fanuc)
    fl = pose * invH(robot.PoseTool())
    cands = []
    for seed in (([prev] if prev is not None else []) + list(SEEDS)):
        q = robot.SolveIK(fl, seed)
        if q is not None:
            cands.append(list(q.list()[:6]))
    for col in (robot.SolveIK_All(fl) or []):
        cands.append([float(v) for v in list(col)[:6]])
    valid = []
    for ql in cands:
        tcp = robot.SolveFK(ql) * robot.PoseTool()
        err = max(abs(tcp[a, b] - pose[a, b]) for a in range(4) for b in range(4))
        if err > 1e-3 or not in_limits(ql):
            continue
        robot.setJoints(ql)
        if (RDK.Collisions() or 0) > 0:
            continue
        valid.append(ql)
    if not valid:
        return None, '无有效候选'
    min_j4 = min(abs(q[3]) for q in valid)
    pool = [q for q in valid if abs(q[3]) <= min_j4 + 20.0]
    if prev is None:
        return pool[0], None
    best = min(pool, key=lambda q: sum(abs(a - b) for a, b in zip(q, prev)))
    return best, None

def eval_delta(delta, verbose=False):
    place_unit(delta)
    prev = [0.0] * 6
    qs = []
    for idx, (x, y, z, rx, ry, rz) in enumerate(TRAJ):
        if abs(y) > 1e-9:
            tgt = (x, y + delta, z + 170.0, rx, ry, rz)
        else:
            tgt = (x, y, z + 170.0, rx, ry, rz)
        ql, err = solve_healthy(tgt, prev)
        if ql is None:
            return None, (idx, err)
        prev = ql
        qs.append(ql)
        if verbose:
            print('  %2d q=[%s] J4=%7.1f' % (idx, ', '.join('%.1f' % v for v in ql), ql[3]))
    return qs, None

print('--- 健康分支扫描 Δ∈[56,166] ---')
ok_deltas = []
for d in range(56, 167, 10):
    qs, fail = eval_delta(float(d))
    if qs is None:
        print('X  Δ=%+4d 线A=%7.1f 点%d %s' % (d, -775 + d, fail[0], fail[1]))
    else:
        maxj4 = max(abs(q[3]) for q in qs)
        print('OK Δ=%+4d 线A=%7.1f 全19点健康解 max|J4|=%.1f' % (d, -775 + d, maxj4))
        ok_deltas.append(d)

assert ok_deltas, '健康域为空'
assert PICK_DELTA in ok_deltas or any(abs(d - PICK_DELTA) <= 11 for d in ok_deltas), '预选 Δ 不在健康域'
print('选定 Δ=+76（线A=-699）')

# ---- 落位 ----
place_unit(PICK_DELTA)
print('落位：圆柱 y=%.1f  挡板 y=%.1f' % (cyl.Pose()[1, 3], baffle.Pose()[1, 3]))

# ---- 全点复核 + 关节表 ----
qs, fail = eval_delta(PICK_DELTA, verbose=True)
assert qs is not None, '落位后复核失败: %r' % (fail,)
print('=== Δ=+76 全19点健康解复核通过 max|J4|=%.1f ===' % max(abs(q[3]) for q in qs))

# ---- 重写轨迹13 ----
out = []
for i, p in enumerate(RAW):
    v = [float(x) for x in p['values']]
    if abs(v[1]) > 1e-9:
        v[1] = v[1] + PICK_DELTA
    v[2] = v[2] + 170.0
    entry = dict(p); entry['values'] = v
    out.append(entry)
with open(DST13, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
    f.write('\n')
print('已重写 %s（Δ=+76 版，19 点）' % DST13)

# ---- 截图（停工作点1）----
robot.setJoints(qs[1])
RDK.Render(True)
time.sleep(2.0)
SHOT = r'D:\mydata\glm-workplace\tools\rdk_traj13_far.png'
if os.path.exists(SHOT): os.remove(SHOT)
r = RDK.Cam2D_Snapshot(SHOT, None)
print('截图 ret=%r size=%d' % (r, os.path.getsize(SHOT) if os.path.exists(SHOT) else -1))
RDK.setRunMode(ORIG_RUNMODE)
print('RunMode -> %r；未保存工作站' % ORIG_RUNMODE)
