#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 终验：直接加载交付文件 sim_scripts\连续轨迹10_修复版.json（保留原始10的全部标记），
# 从原点规划，确认与 C 方案（8+9拼接版）结果一致。
import sys, io, json, ast, math, time, re
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace",
                              line_buffering=True)
from robodk.robolink import *
from robodk.robomath import *

SRC = r"D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py"
FIXED = r"D:\mydata\glm-workplace\sim_scripts\连续轨迹10_修复版.json"
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

data = json.load(open(FIXED, encoding="utf-8"))
recs = []
for item in data:
    is_s = bool(item.get("singular", False)) and item["type"] == "TCP"
    is_spin = is_s and bool(item.get("spin360", False))
    raw_d = int(item.get("j6_delta", 360 if is_spin else 180)) if is_s else 0
    recs.append({"type": item["type"], "values": item["values"][:],
                 "target": ns["fanuc_values_to_pose"](*item["values"]) if item["type"] == "TCP" else None,
                 "joints": None, "singular": is_s, "spin360": is_spin,
                 "j6_delta": ((360 if is_spin else 180) * (1 if raw_d >= 0 else -1)) if is_s else 0})

try:
    robot.setJoints(ORIGIN)
    records = ns["_retreat_orientation_records"](recs)
    print("== [交付版10_修复] %d原始点 -> %d执行点，从原点 ==" % (len(recs), len(records)), flush=True)
    lines = []
    def log(m):
        s = str(m)
        lines.append(s)
        if "快速筛选" in s or "未通过" in s:
            print("  |", s, flush=True)
    t0 = time.time()
    try:
        plan = ns["_plan_continuous_trajectory"](records, 500.0, log)
        print("== [交付版10_修复] 结果: PASS  %d步  %.1fs ==" % (len(plan), time.time() - t0), flush=True)
    except Exception as exc:
        cnt = Counter()
        for s in lines:
            m = re.match(r"候选分支未通过：P(\d+)", s)
            if m:
                cnt[int(m.group(1))] += 1
        print("== [交付版10_修复] 结果: FAIL  %.1fs ==" % (time.time() - t0), flush=True)
        print("   最终错误: %s" % str(exc)[:200], flush=True)
        print("   死点分布(展P:次数): %s" % dict(sorted(cnt.items())), flush=True)
finally:
    robot.setJoints(PARKED)
    print("== 终验结束，已还原停放关节 ==", flush=True)
