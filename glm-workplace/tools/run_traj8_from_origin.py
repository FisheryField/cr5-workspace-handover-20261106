#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 从关节原点(零位)规划并执行 连续轨迹8（副本脚本同款规划器）。
# 结束后把模型关节还原到用户停放位姿。flush输出防超时空白。
import sys, io, json, ast, math, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace",
                              line_buffering=True)
from robodk.robolink import *
from robodk.robomath import *

SRC = r"D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py"
PARKED = [-13.592, 82.073, -74.949, 82.876, -90.000, -193.592]  # 轨迹9终点(用户停放)

tree = ast.parse(open(SRC, encoding="utf-8").read())
KEEP_ASSIGN = {"SIM_SPEED", "ALLOW_SIMULATION", "MOVEJ_FALLBACK_MAX_DEVIATION_MM",
               "_plan_cache", "RDK", "robot", "target_pose", "target_joints",
               "simulation_running", "trajectory_records"}
ns = {}
for node in tree.body:
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        mods = ([a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""])
        if any(m.split(".")[0] == "tkinter" for m in mods):
            continue
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                         ast.Import, ast.ImportFrom)):
        exec(compile(ast.Module(body=[node], type_ignores=[]), SRC, "exec"), ns)
    elif isinstance(node, ast.Assign) and all(isinstance(t, ast.Name) and t.id in KEEP_ASSIGN for t in node.targets):
        exec(compile(ast.Module(body=[node], type_ignores=[]), SRC, "exec"), ns)
ns["math"] = math

RDK, robot = ns["RDK"], ns["robot"]
cur = robot.Joints().list()[:6]
print("当前关节:", ["%.3f" % v for v in cur], flush=True)
if max(abs(a - b) for a, b in zip(cur, PARKED)) > 0.01:
    print("!! 上次被杀的矩阵脚本把关节留在半路，先还原停放位", flush=True)
    robot.setJoints(PARKED)

def load(path):
    data = json.load(open(path, encoding="utf-8"))
    recs = []
    for item in data:
        is_s = bool(item.get("singular", False)) and item["type"] == "TCP"
        is_spin = is_s and bool(item.get("spin360", False))
        raw_d = int(item.get("j6_delta", 360 if is_spin else 180)) if is_s else 0
        recs.append({"type": item["type"], "values": item["values"][:],
                     "target": ns["fanuc_values_to_pose"](*item["values"]) if item["type"] == "TCP" else None,
                     "joints": None, "singular": is_s, "spin360": is_spin,
                     "j6_delta": ((360 if is_spin else 180) * (1 if raw_d >= 0 else -1)) if is_s else 0})
    return recs

recs = load(r"D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹8.json")

ORIGIN = [0.0] * 6
robot.setJoints(ORIGIN)
tcp0 = invH(robot.PoseFrame()) * robot.SolveFK(ORIGIN) * robot.PoseTool()
print("原点 FK TCP(base):", " ".join("%9.3f" % v for v in tcp0.Pos()), flush=True)

records = ns["_retreat_orientation_records"](recs)
print("轨迹8：%d 原始点 -> %d 执行点" % (len(recs), len(records)), flush=True)

t0 = time.time()
last = []
def log(m):
    s = str(m)
    print("  |", s, flush=True)

try:
    plan = ns["_plan_continuous_trajectory"](records, 500.0, log)
    print("== 预检 PASS：%d 步，用时 %.1fs ==" % (len(plan), time.time() - t0), flush=True)
    for i, st in enumerate(plan, 1):
        print("  step%-3d %-6s J6=%+9.3f special=%-5s delta=%s" % (
            i, st["method"], st["joints"][5], st["special"], st["j6_delta"]), flush=True)

    # ---- 执行（与 GUI execute_recorded_trajectory 同口径：先回绕后主步）----
    RDK.setRunMode(RUNMODE_SIMULATE)
    robot.setSpeed(300.0)
    print("== 开始执行（仿真模式，提速300）==", flush=True)
    for i, step in enumerate(plan, 1):
        for rewound in step["rewinds"]:
            before = robot.Joints().list()[:6]
            print("P%d前回绕J6 %+d°（%+.1f -> %+.1f）" % (
                i, rewound[5] - before[5], before[5], rewound[5]), flush=True)
            robot.MoveJ(rewound)
        getattr(robot, step["method"])(step["joints"])
        actual = robot.Joints().list()[:6]
        dev = max(abs(a - b) for a, b in zip(actual, step["joints"]))
        if dev > 0.1:
            raise RuntimeError("P%d 实际关节与预检终点偏差 %.3f°" % (i, dev))
        print("P%-3d %s 完成" % (i, step["method"]), flush=True)
    qe = robot.Joints().list()[:6]
    tcpe = invH(robot.PoseFrame()) * robot.SolveFK(qe) * robot.PoseTool()
    print("== 执行完成，终点关节:", ["%.3f" % v for v in qe], flush=True)
    print("== 终点 TCP(base):", " ".join("%9.3f" % v for v in tcpe.Pos()), flush=True)
finally:
    robot.setJoints(PARKED)
    print("已还原停放关节:", ["%.3f" % v for v in robot.Joints().list()[:6]], flush=True)
