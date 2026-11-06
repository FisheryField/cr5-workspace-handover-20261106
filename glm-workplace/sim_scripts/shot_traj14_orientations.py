# -*- coding: utf-8 -*-
"""轨迹14 姿态巡拍（2026-10-20）：仿真模式下逐点走位 + Cam2D_Snapshot 出图。
- 只在 RUNMODE_SIMULATE 里 MoveJ（不动实机）；不改站、不保存。
- 用 SolveIK(..., joints_approx=上一点关节) 保持分支连续。
- 输出 tools\\traj14_shots\\traj14_Pxx_<标签>.png
"""
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import *
from robodk.robomath import Fanuc_2_Pose

OUTDIR = r'D:\mydata\glm-workplace\tools\traj14_shots'
os.makedirs(OUTDIR, exist_ok=True)
JSON = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹14.json'

# 要拍的点与其标签（其余点姿态重复）
SHOTS = [
    (1,  'P1_park_start'),
    (2,  'P2_slide_start'),
    (3,  'P3_slide_plusX'),
    (4,  'P4_flip_atX100'),
    (5,  'P5_slide_back'),
    (8,  'P8_downface_start'),
    (10, 'P10_downface_slideX'),
    (11, 'P11_downface_flip'),
    (18, 'P18_spin_prep'),
    (21, 'P21_park_end'),
]

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
assert robot.Valid()
frame = robot.PoseFrame()
tool = Fanuc_2_Pose([0.0, 0.0, 182.0, 0.0, 0.0, 0.0])

RDK.setRunMode(RUNMODE_SIMULATE)
RDK.setCollisionActive(False)   # 拍照只看姿态；路径安全性已由预检权威背书

recs = json.load(open(JSON, encoding='utf-8'))

def ik(vals, approx):
    if approx is None:
        q = robot.SolveIK(Fanuc_2_Pose(vals), tool=tool, reference=frame)
    else:
        q = robot.SolveIK(Fanuc_2_Pose(vals), approx, tool=tool, reference=frame)
    try:
        t = q.tolist()
    except Exception:
        t = []
    flat = []
    for v in t:
        flat.extend(v if isinstance(v, (list, tuple)) else [v])
    return flat[:6] if len(flat) >= 6 else None

# 先按全轨迹顺序求解一遍（保持分支连续），再对目标点拍照
approx = None
solved = {}
for i, rec in enumerate(recs, 1):
    q = ik([float(v) for v in rec['values']], approx)
    if q is None:
        print('P%d IK 无解（跳过并保持上一姿态）' % i)
        continue
    solved[i] = q
    approx = q

made = []
for i, tag in SHOTS:
    if i not in solved:
        print('P%d 无解，未拍' % i)
        continue
    robot.MoveJ(solved[i])                      # 仿真走位
    path = os.path.join(OUTDIR, 'traj14_%s.png' % tag)
    if os.path.exists(path):
        os.remove(path)
    r = RDK.Cam2D_Snapshot(path, None)
    ok = os.path.exists(path) and os.path.getsize(path) > 0
    print('P%-2d %-18s snapshot=%r  %s' % (i, tag, r, ('%d B' % os.path.getsize(path)) if ok else 'FAIL'))
    if ok:
        made.append(path)

# 复位仿真机器人到零位姿态（不回零实机；仅仿真显示）
robot.MoveJ([0, 0, 0, 0, 0, 0])
print('DONE  共 %d 张 → %s' % (len(made), OUTDIR))
