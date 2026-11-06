#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 原点对照套件：从关节零位依次规划 连续轨迹8 / 9 / 10（只规划不执行）。
# 每条之间还原用户停放位，保证种子一致。结束还原停放位。
import sys, io, json, ast, math, time, re
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace",
                              line_buffering=True)
from robodk.robolink import *
from robodk.robomath import *

SRC = r"D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py"
PARKED = [-13.592, 82.073, -74.949, 82.876, -90.000, -193.592]
ORIGIN = [0.0] * 6

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

BASE = r"D:\mydata\working things\dobot_arm\RoboDK files 2"

def run_one(name):
    recs = load((BASE + r"\连续轨迹%s.json") % name)
    robot.setJoints(ORIGIN)
    records = ns["_retreat_orientation_records"](recs)
    print("== [%s] %d原始点 -> %d执行点，从原点开始 ==" % (name, len(recs), len(records)), flush=True)
    lines = []
    def log(m):
        s = str(m)
        lines.append(s)
        if "快速筛选" in s or "未通过" in s:
            print("  |", s, flush=True)
    t0 = time.time()
    try:
        plan = ns["_plan_continuous_trajectory"](records, 500.0, log)
        print("== [%s] 结果: PASS  %d步  %.1fs ==" % (name, len(plan), time.time() - t0), flush=True)
        return True
    except Exception as exc:
        cnt = Counter()
        for s in lines:
            m = re.match(r"候选分支未通过：P(\d+)", s)
            if m:
                cnt[int(m.group(1))] += 1
        print("== [%s] 结果: FAIL  %.1fs ==" % (name, time.time() - t0), flush=True)
        print("   最终错误: %s" % str(exc)[:200], flush=True)
        print("   死点分布(展P:次数): %s" % dict(sorted(cnt.items())), flush=True)
        return False
    finally:
        robot.setJoints(PARKED)

try:
    for name in ("8", "9", "10"):
        run_one(name)
        print("", flush=True)
finally:
    robot.setJoints(PARKED)
    print("== 套件结束，已还原停放关节 ==", flush=True)
