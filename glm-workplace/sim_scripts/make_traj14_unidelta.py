# -*- coding: utf-8 -*-
"""轨迹14 终版生成（2026-10-20 用户约束）：
- 基底 = 轨迹13 原版；P1/P21 不动；P2–P20 统一 y += Δ（x/z 完全不变，z 含 570 点）；
- Δ 求法：逐点实测「朝 +y（基座侧）到可解」的最小 Δ_i（tool=182），取 max + 10mm 余量（5 取整）；
- 全部 19 点在最终 Δ 下复核可解 → 写 连续轨迹14.json → 打印逐点表。
"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT
from robodk.robomath import Fanuc_2_Pose

SRC = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹13.json'
DST = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹14.json'

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
frame = robot.PoseFrame()
tool = Fanuc_2_Pose([0.0, 0.0, 182.0, 0.0, 0.0, 0.0])

def solvable(x, y, z, rx, ry, rz):
    q = robot.SolveIK(Fanuc_2_Pose([float(x), float(y), float(z), float(rx), float(ry), float(rz)]),
                      tool=tool, reference=frame)
    try:
        t = q.tolist()
    except Exception:
        t = []
    flat = []
    for v in t:
        flat.extend(v if isinstance(v, (list, tuple)) else [v])
    return len(flat) >= 6

recs = json.load(open(SRC, encoding='utf-8'))
assert len(recs) == 21

print('逐点所需 Δ_i（原位不可解时=朝+5 步进到可解；原位已可解=0）:')
deltas = {}
for i, rec in enumerate(recs, 1):
    if i in (1, 21):
        continue
    v = [float(t) for t in rec['values']]
    if solvable(v[0], v[1], v[2], v[3], v[4], v[5]):
        deltas[i] = 0.0
        continue
    y = v[1]; steps = 0.0
    while steps <= 300.0:
        y += 5.0; steps += 5.0
        if solvable(v[0], y, v[2], v[3], v[4], v[5]):
            deltas[i] = steps
            break
    else:
        deltas[i] = float('inf')
    print('  P%-2d 原 y=%7.1f z=%3.0f rx=%5.0f  需 Δ≥+%.0f' % (i, v[1], v[2], v[3], deltas[i]))

worst = max(deltas.values())
if worst == float('inf'):
    print('!!! 有点在 +300 内无解，中止')
    sys.exit(1)
delta = (worst + 10.0) // 5 * 5
if worst == 0.0:
    delta = 0.0
print('需求 max Δ_i = +%.0f  ⇒  取 Δ = +%.0f（+10 余量，5 取整）' % (worst, delta))

# 生成
out = []
all_ok = True
for i, rec in enumerate(recs, 1):
    v = [float(t) for t in rec['values']]
    if i not in (1, 21):
        v[1] += delta
        if not solvable(v[0], v[1], v[2], v[3], v[4], v[5]):
            all_ok = False
            print('  复核 P%d ✗ 仍不可解' % i)
    e = dict(rec); e['values'] = v
    out.append(e)
    print('P%-2d (%7.1f,%7.1f,%5.1f,%6.1f,%4.1f,%6.1f)' % (i, v[0], v[1], v[2], v[3], v[4], v[5]))

if not all_ok:
    print('!!! 复核失败，不写盘')
    sys.exit(1)

with open(DST, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(out, f, indent=2, ensure_ascii=False); f.write('\n')
print('已写入:', DST, '  Δ = +%.0f mm' % delta)
