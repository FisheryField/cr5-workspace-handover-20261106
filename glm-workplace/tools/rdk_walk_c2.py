#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C 方案姿态族的 IK 预检 + 找可行解 + 走位 + 快照 + 回原位。"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from robodk import robolink, robomath

RDK = robolink.Robolink()
robot = RDK.Item("Dobot CR5", robolink.ITEM_TYPE_ROBOT)
state_raw = robot.ConnectedState()
state = state_raw[0] if isinstance(state_raw, tuple) else state_raw
if state not in (robolink.ROBOTCOM_DISCONNECTED, robolink.ROBOTCOM_NOT_CONNECTED, -1, 0, None):
    print("ABORT: 已连真机"); sys.exit(2)
RDK.setRunMode(robolink.RUNMODE_SIMULATE)

def faces_report(tag):
    T = robot.Pose()
    zcol = [T[0, 2], T[1, 2], T[2, 2]]
    tcp = [T[0, 3], T[1, 3], T[2, 3]]
    fn = [tcp[k] - 12.3 * zcol[k] for k in range(3)]
    fp = [tcp[k] + 12.3 * zcol[k] for k in range(3)]
    ycol = [T[0, 1], T[1, 1], T[2, 1]]
    neck = [tcp[k] + 59.5 * ycol[k] for k in range(3)]
    xcol = [T[0, 0], T[1, 0], T[2, 0]]
    tip = [tcp[k] + 107.8 * xcol[k] for k in range(3)]
    print("[%s] -Z面y=%.2f gap=%+.2f | +Z面y=%.2f gap=%+.2f | 颈尖=(%.0f,%.0f,%.0f) 臂尖=(%.0f,%.0f,%.0f)" % (
        tag, fn[1], fn[1] + 776, fp[1], fp[1] + 776, neck[0], neck[1], neck[2], tip[0], tip[1], tip[2]))

# 预检候选姿态族
print("== IK 预检 ==")
feasible = []
for rx in (-180, -90, 0, 90, 180):
    for rz in (-180, -90, 0, 90, 180):
        vals = [0, -762.7, 300, rx, 0, rz]
        pose = robomath.xyzrpw_2_pose(vals)
        try:
            ik = robot.SolveIK(pose)
            ikl = ik.list() if hasattr(ik, "list") else list(ik)
            ok = len(ikl) == 6 and all(q == q for q in ikl)
        except Exception:
            ok = False
        if ok:
            T = pose
            zcol = [T[0, 2], T[1, 2], T[2, 2]]
            fz_dir = -zcol[1]
            feasible.append((vals, fz_dir))
            print("  可达 (%4d,0,%4d)  法兰-Z面y方向=%+.2f  j=%s" % (rx, rz, fz_dir, [round(x,1) for x in ikl]))

# 选 -Z 面朝轮的解（fz_dir 最负）
cands = [f for f in feasible if f[1] < -0.9]
print()
print("== -Z面贴轮候选:", [f[0][3:] for f in cands])
if cands:
    vals = cands[0][0]
    print("选用:", vals)
    robot.MoveJ(robomath.xyzrpw_2_pose(vals), blocking=True)
    faces_report("C选中 (%d,0,%d)" % (vals[3], vals[5]))
    print("  关节:", [round(x, 3) for x in robot.Joints().list()])
    RDK.Command("SnapShot", r"D:\mydata\glm-workplace\data\screens\rdk_view_C.png")
    print("SnapShot C 已导出")

# 回原位
j0 = json.load(open(r"D:\mydata\glm-workplace\data\scripts_ref\sim_walk_j0.json", encoding="utf-8"))
robot.MoveJ(j0, blocking=True)
print("已回原位, 关节:", [round(x, 3) for x in robot.Joints().list()])
print("done")
