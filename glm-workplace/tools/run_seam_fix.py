#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 接缝修复验证（都从原点规划）：
#   C = 8+9 拼接，在接缝斜线 (0,-462,400)->(40,-750,300) 中插两个高处平移点：
#       (40,-462,400,90,0,90) 与 (40,-750,400,90,0,90)
#   D = 备选：翻转挪到远角：先 (180,0,180) 朝向平移到 (40,-750,400) 再翻成 (90,0,90) 再降
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

def load_raw(path):
    return json.load(open(path, encoding="utf-8"))

def tcp(v, sing=False, spin=False, d=0):
    return {"type": "TCP", "values": [float(x) for x in v],
            "singular": sing, "spin360": spin, "j6_delta": d}

def to_recs(items):
    recs = []
    for item in items:
        is_s = bool(item.get("singular", False)) and item["type"] == "TCP"
        is_spin = is_s and bool(item.get("spin360", False))
        raw_d = int(item.get("j6_delta", 360 if is_spin else 180)) if is_s else 0
        recs.append({"type": item["type"], "values": item["values"][:],
                     "target": ns["fanuc_values_to_pose"](*item["values"]) if item["type"] == "TCP" else None,
                     "joints": None, "singular": is_s, "spin360": is_spin,
                     "j6_delta": ((360 if is_spin else 180) * (1 if raw_d >= 0 else -1)) if is_s else 0})
    return recs

BASE = r"D:\mydata\working things\dobot_arm\RoboDK files 2"
j8 = load_raw(BASE + r"\连续轨迹8.json")
j9 = load_raw(BASE + r"\连续轨迹9.json")

def same(p, q, tol=1e-6):
    return all(abs(float(x) - float(y)) <= tol for x, y in zip(p["values"], q["values"]))
skip = 0
for k in range(len(j9)):
    if same(j8[-1], j9[k]):
        skip = k + 1
    else:
        break
tail = j9[skip:]

# C: 在 tail[1]((0,-462,400,90,0,90)) 与 tail[2]((40,-750,300,90,0,90)) 之间插两个高点
VAR_C = to_recs(j8 + tail[:2] + [
    tcp([40, -462, 400, 90, 0, 90]),
    tcp([40, -750, 400, 90, 0, 90]),
] + tail[2:])

# D: 备选——保持 (180,0,180) 朝向平移，到 (40,-750,400) 后再翻 (90,0,90)，再竖直降
VAR_D = to_recs(j8 + [
    tail[0],                                  # (0,-462,400,180,0,180)
    tcp([40, -462, 400, 180, 0, 180]),
    tcp([40, -750, 400, 180, 0, 180]),
    tcp([40, -750, 400, 90, 0, 90]),
] + tail[2:])                                # (40,-750,300,90,0,90) 起，余同

def run_one(tag, recs):
    robot.setJoints(ORIGIN)
    records = ns["_retreat_orientation_records"](recs)
    print("== [%s] %d原始点 -> %d执行点，从原点 ==" % (tag, len(recs), len(records)), flush=True)
    lines = []
    def log(m):
        s = str(m)
        lines.append(s)
        if "快速筛选" in s or "未通过" in s:
            print("  |", s, flush=True)
    t0 = time.time()
    try:
        plan = ns["_plan_continuous_trajectory"](records, 500.0, log)
        print("== [%s] 结果: PASS  %d步  %.1fs ==" % (tag, len(plan), time.time() - t0), flush=True)
        return True
    except Exception as exc:
        cnt = Counter()
        for s in lines:
            m = re.match(r"候选分支未通过：P(\d+)", s)
            if m:
                cnt[int(m.group(1))] += 1
        print("== [%s] 结果: FAIL  %.1fs ==" % (tag, time.time() - t0), flush=True)
        print("   最终错误: %s" % str(exc)[:200], flush=True)
        print("   死点分布(展P:次数): %s" % dict(sorted(cnt.items())), flush=True)
        return False
    finally:
        robot.setJoints(PARKED)

try:
    run_one("C: 插高点平移", VAR_C)
    print("", flush=True)
    run_one("D: 远角翻转", VAR_D)
finally:
    robot.setJoints(PARKED)
    print("== 接缝修复验证结束，已还原停放关节 ==", flush=True)
