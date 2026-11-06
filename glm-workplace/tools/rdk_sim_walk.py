#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""仿真试走：让 RoboDK 模型走到把手背面贴砂轮的 TCP 坐标。
用法: python rdk_sim_walk.py <phase>
  phase gate : 安全闸 + IK 预检，不动任何东西
  phase A    : MoveJ 到 (0,-762.7,300,-90,0,180)   [背面=局部-Z]
  phase B    : MoveJ 到 (0,-762.7,300, 90,0,0)     [背面=局部+Z]
  phase home : 回 gate 时存档的原始关节角
约束：绝不 Connect、绝不下发真机、绝不改脚本/站点文件。"""
import sys, io, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from robodk import robolink, robomath

PHASE = sys.argv[1] if len(sys.argv) > 1 else "gate"
J0_FILE = r"D:\mydata\glm-workplace\data\scripts_ref\sim_walk_j0.json"
POSE_A = [0, -762.7, 300, -90, 0, 180]
POSE_B = [0, -762.7, 300, 90, 0, 0]

RDK = robolink.Robolink()
robot = RDK.Item("Dobot CR5", robolink.ITEM_TYPE_ROBOT)
if not robot.Valid():
    print("FATAL: robot item not found"); sys.exit(1)

state_raw = robot.ConnectedState()
state = state_raw[0] if isinstance(state_raw, tuple) else state_raw
print("ConnectedState =", state_raw)
if state not in (robolink.ROBOTCOM_DISCONNECTED, robolink.ROBOTCOM_NOT_CONNECTED, -1, 0, None):
    print("ABORT: RoboDK 已连接真机驱动，本任务只允许仿真。", flush=True); sys.exit(2)
print("安全闸通过：驱动未连真机，仅仿真。")

RDK.setRunMode(robolink.RUNMODE_SIMULATE)
print("RunMode = SIMULATE")

if PHASE == "gate":
    j = robot.Joints().list()
    print("当前关节:", [round(x, 3) for x in j])
    with open(J0_FILE, "w", encoding="utf-8") as f:
        json.dump(j, f)
    print("已存档原始关节角 ->", J0_FILE)
    for name, vals in [("A(-Z面)", POSE_A), ("B(+Z面)", POSE_B)]:
        pose = robomath.xyzrpw_2_pose(vals)
        ik = robot.SolveIK(pose)
        ikl = ik.list() if hasattr(ik, "list") else list(ik)
        ok = all(q == q for q in ikl) and len(ikl) == 6
        print("方案 %s %s IK可达=%s 解=%s" % (name, vals, ok,
              [round(x, 2) for x in ikl] if ok else ikl))

elif PHASE in ("A", "B"):
    vals = POSE_A if PHASE == "A" else POSE_B
    pose = robomath.xyzrpw_2_pose(vals)
    robot.MoveJ(pose, blocking=True)
    p = robot.Pose()
    print("MoveJ %s 完成" % PHASE)
    print("到达法兰位姿:\n", p)
    j = robot.Joints().list()
    print("关节:", [round(x, 3) for x in j])
    T = p
    zcol = [T[0, 2], T[1, 2], T[2, 2]]
    tcp = [T[0, 3], T[1, 3], T[2, 3]]
    face_neg = [tcp[k] - 12.3 * zcol[k] for k in range(3)]
    face_pos = [tcp[k] + 12.3 * zcol[k] for k in range(3)]
    print("把手局部-Z面中心全局: (%.2f, %.2f, %.2f)" % tuple(face_neg))
    print("把手局部+Z面中心全局: (%.2f, %.2f, %.2f)" % tuple(face_pos))
    print("砂轮轮缘 y=-776（工作约定 y=-775）")
    for nm, f in [("-Z面", face_neg), ("+Z面", face_pos)]:
        print("  %s 距轮缘间隙 = %.2f mm" % (nm, f[1] - (-776)))

elif PHASE == "home":
    if not os.path.exists(J0_FILE):
        print("没有存档 j0，跳过"); sys.exit(0)
    j0 = json.load(open(J0_FILE, encoding="utf-8"))
    robot.MoveJ(j0, blocking=True)
    print("已回到原始关节:", [round(x, 3) for x in robot.Joints().list()])

else:
    print("unknown phase")
