# -*- coding: utf-8 -*-
"""轨迹14 终版 v2（2026-10-20 用户新约束）：
- P1/P21 不动；P2–P20：x 不变、y 统一 +Δ、z 统一为同一个 Z（原 470/570 混合 → 拉平到 Z）；
- 目标：尽量远（Δ 尽量小，可为 0 或负）；扫描 Z 阶梯 → 每档求 Δ_needed；
- 选定 Z*（能使全部点在 Δ=−10 处仍可解的最低 15mm 档）→ 取 Δ=0（原深度）；
- 场景同步：面表 = −700+Δ（1mm 贴面惯例）⇒ 从当前 −625 移到目标；
- 写 连续轨迹14.json。
"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT
from robodk.robomath import Fanuc_2_Pose, Pose_2_Fanuc

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
pts = []
for i, rec in enumerate(recs, 1):
    if i in (1, 21):
        continue
    v = [float(t) for t in rec['values']]
    pts.append((i, v))

def needed_delta(Z):
    """返回 (Δ_needed 最大正值需求, 全点共同的最远可解 Δ 上界 bound)。
    bound ≤ −10 ⇒ Δ=0 时全部点仍有 ≥10mm 远向余量。"""
    need = 0.0
    bound = None
    for i, v in pts:
        x, y0, rx, ry, rz = v[0], v[1], v[3], v[4], v[5]
        if solvable(x, y0, Z, rx, ry, rz):
            d = 0.0
            while d > -260.0 and solvable(x, y0 + d - 5.0, Z, rx, ry, rz):
                d -= 5.0
            b = d
        else:
            d = 0.0
            while d < 300.0:
                d += 5.0
                if solvable(x, y0 + d, Z, rx, ry, rz):
                    break
            need = max(need, d)
            b = d          # 不可解侧的边界即需求点
        bound = b if bound is None else max(bound, b)
    return need, bound

print('%-6s %-10s %-12s' % ('Z', 'Δ_needed', '最远bound Δ'))
best = None
for Z in (470.0, 455.0, 440.0, 425.0, 410.0, 395.0, 380.0, 365.0, 350.0):
    need, bound = needed_delta(Z)
    print('%-6.0f %-10.0f %-12.0f' % (Z, need, bound))
    if best is None and need <= 0.0 and bound <= -10.0:
        best = Z
print('选定 Z* =', best)

if best is None:
    print('!!! 扫描范围内无 Z 能让 Δ≤0 且留 10mm 远余量；中止（可放宽 Z 下限再议）')
    sys.exit(1)

Z = best
DELTA = 0.0

# 场景同步：面表 = −700 + Δ ⇒ 需要 cylinder face 到 −700
# 当前面表实测 = −625（pose.y −765）；face = pose.y + 140
target_pose_y = -700.0 - 140.0   # −840
cur_cyl_y = Pose_2_Fanuc(RDK.Item('磨砂圆柱_R150_H50').Pose())[1]
shift = target_pose_y - cur_cyl_y
for name in ['磨砂圆柱_R150_H50', '挡板_半封闭3面']:
    it = RDK.Item(name)
    p = Pose_2_Fanuc(it.Pose())
    it.setPose(Fanuc_2_Pose([p[0], p[1] + shift, p[2], p[3], p[4], p[5]]))
print('场景 y 平移 %+.0f（圆柱 pose.y %.0f→%.0f，面表→−700）' % (
    shift, cur_cyl_y, Pose_2_Fanuc(RDK.Item('磨砂圆柱_R150_H50').Pose())[1]))

out = []
for i, rec in enumerate(recs, 1):
    v = [float(t) for t in rec['values']]
    if i not in (1, 21):
        v[1] += DELTA
        v[2] = Z
        assert solvable(v[0], v[1], v[2], v[3], v[4], v[5]), 'P%d 复核不可解' % i
    e = dict(rec); e['values'] = v
    out.append(e)
    print('P%-2d (%7.1f,%7.1f,%5.1f,%6.1f,%4.1f,%6.1f)' % (i, v[0], v[1], v[2], v[3], v[4], v[5]))

with open(DST, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(out, f, indent=2, ensure_ascii=False); f.write('\n')
print('已写入:', DST, ' Z=%d, Δ=0（原深度）, 未保存工作站' % Z)
