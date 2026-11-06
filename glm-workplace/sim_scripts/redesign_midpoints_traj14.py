# -*- coding: utf-8 -*-
"""轨迹14 中间点重设计（2026-10-21）：
P6/P7（A簇→B簇的姿态过渡）与 P13/P14/P15（B簇→rz90 尾段过渡）在 z=380 低空换姿导致长 MoveJ 绕行。
在候选网格上搜索关节行程最小且 MoveJ 路径无碰的过渡点组合，替换后写回轨迹14。
- 锚点：P5、P8、P12、P16 保持不变；中间点位置/高度自由（含抬高到 380~520）。
- 代价：|q_prev−q_m1|+|q_m1−q_m2|(+…)+|q_last−q_next| 的关节 L1 和；分支用 SolveIK_All 全枚举。
"""
import sys, io, json, math, itertools
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk.robolink import *
from robodk.robomath import Fanuc_2_Pose

JSON = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹14.json'
RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
frame = robot.PoseFrame()
tool = Fanuc_2_Pose([0.0, 0.0, 182.0, 0.0, 0.0, 0.0])
J4MAX, J5MIN = 100.0, 165.0

RDK.setRunMode(RUNMODE_SIMULATE)
RDK.setCollisionActive(True)
for name in ('安装台_650x650x80mm', '地面_禁止穿越', '磨砂圆柱_R150_H50', '挡板_半封闭3面'):
    obstacle = RDK.Item(name, ITEM_TYPE_OBJECT)
    if name == '安装台_650x650x80mm':
        RDK.setCollisionActivePair(COLLISION_OFF, robot, obstacle, 0, 0)
    for link in range(1, 7):
        RDK.setCollisionActivePair(COLLISION_ON, robot, obstacle, link, 0)
_h = RDK.Item('门把手_bs1')
for link in range(1, 7):
    RDK.setCollisionActivePair(1, robot, _h, link, 0)

def all_ik(vals):
    q = robot.SolveIK_All(Fanuc_2_Pose([float(v) for v in vals]), tool=tool, reference=frame)
    try:
        rows = q.rows
    except Exception:
        return []
    if not rows or len(rows) < 6:
        return []
    n = len(rows[0])
    out = []
    for c in range(n):
        sol = [rows[r][c] for r in range(6)]
        if any(abs(sol[3]) > J4MAX and abs(sol[4]) > J5MIN for _ in [0]):
            continue   # 自干涉组合区弃用
        out.append(sol)
    return out

def jdist(a, b):
    return sum(abs(x - y) for x, y in zip(a, b))

def path_ok(a, b):
    return robot.MoveJ_Test(a, b, minstep_deg=3) == 0

recs = json.load(open(JSON, encoding='utf-8'))
V = {i: [float(t) for t in recs[i - 1]['values']] for i in range(1, 22)}

# 锚点分支集合
A5 = all_ik(V[5]); A8 = all_ik(V[8]); A12 = all_ik(V[12]); A16 = all_ik(V[16])
print('锚点分支数: P5=%d P8=%d P12=%d P16=%d' % (len(A5), len(A8), len(A12), len(A16)))
assert A5 and A8 and A12 and A16

# ---------- 槽1：P6/P7（P5→过渡→P8），P6=(90,0,0) 同P5向，P7=(180,0,0) ----------
cands1 = []
for y in (-520.0, -550.0, -580.0, -610.0, -640.0, -670.0):
    for z in (380.0, 420.0, 460.0, 500.0):
        cands1.append((0.0, y, z))
best1 = None
for (x, y, z) in cands1:
    m1s = all_ik([x, y, z, 90, 0, 0])
    m2s = all_ik([x, y, z, 180, 0, 0])
    for q5 in A5:
        for q8 in A8:
            for qm1 in m1s:
                if jdist(q5, qm1) > 200: continue
                if not path_ok(q5, qm1): continue
                for qm2 in m2s:
                    c = jdist(q5, qm1) + jdist(qm1, qm2) + jdist(qm2, q8)
                    if best1 and c >= best1[0]: continue
                    if not path_ok(qm1, qm2): continue
                    if not path_ok(qm2, q8): continue
                    best1 = (c, (x, y, z), qm1, qm2)
    print('槽1 扫过 y=%.0f z=%.0f  当前最优=%.1f' % (y, z, best1[0] if best1 else -1))
print('槽1 最优:', None if not best1 else ('%.0f,%.0f,%.0f cost=%.1f' % (best1[1][0], best1[1][1], best1[1][2], best1[0])))

# ---------- 槽2：P13/P14/P15（P12→过渡→P16） ----------
# P13=(…,180,180) 撤；P14=(…,90,90) 换向；P15=(40, …,90,90) x 对齐 P16
cands2 = []
for y in (-520.0, -550.0, -580.0, -610.0, -640.0):
    for z in (380.0, 420.0, 460.0, 500.0):
        cands2.append((0.0, y, z))
best2 = None
for (x, y, z) in cands2:
    m1s = all_ik([x, y, z, 180, 0, 180])
    m2s = all_ik([x, y, z, 90, 0, 90])
    m3s = all_ik([40.0, y, z, 90, 0, 90])
    for q12 in A12:
        for q16 in A16:
            for qm1 in m1s:
                if not path_ok(q12, qm1): continue
                for qm2 in m2s:
                    if not path_ok(qm1, qm2): continue
                    for qm3 in m3s:
                        if not path_ok(qm2, qm3): continue
                        c = jdist(q12, qm1) + jdist(qm1, qm2) + jdist(qm2, qm3) + jdist(qm3, q16)
                        if best2 and c >= best2[0]: continue
                        if not path_ok(qm3, q16): continue
                        best2 = (c, (x, y, z), qm1, qm2, qm3)
    print('槽2 扫过 y=%.0f z=%.0f  当前最优=%.1f' % (y, z, best2[0] if best2 else -1))
print('槽2 最优:', None if not best2 else ('%.0f,%.0f,%.0f cost=%.1f' % (best2[1][0], best2[1][1], best2[1][2], best2[0])))

if not best1 or not best2:
    print('!!! 至少一个槽无可行解，中止不写盘')
    sys.exit(1)

x1, y1, z1 = best1[1]
x2, y2, z2 = best2[1]
# 写回：P6/P7=(x1,y1,z1)，P13=(x2,y2,z2,180,180)，P14=(x2,y2,z2,90,90)，P15=(40,y2,z2,90,90)
recs[5]['values'] = [x1, y1, z1, 90.0, 0.0, 0.0]
recs[6]['values'] = [x1, y1, z1, 180.0, 0.0, 0.0]
recs[12]['values'] = [x2, y2, z2, 180.0, 0.0, 180.0]
recs[13]['values'] = [x2, y2, z2, 90.0, 0.0, 90.0]
recs[14]['values'] = [40.0, y2, z2, 90.0, 0.0, 90.0]
with open(JSON, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(recs, f, indent=2, ensure_ascii=False); f.write('\n')
print('已写回轨迹14：P6/P7=(%.0f,%.0f,%.0f)  P13/14=(%.0f,%.0f,%.0f) P15 x=40' % (x1, y1, z1, x2, y2, z2))
print('DONE')
