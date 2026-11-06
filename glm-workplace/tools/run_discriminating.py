#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 判别实验（都从原点规划）：
#   A = 干净8 + 9 原样拼接（无自转、无多余标记）
#   B = 轨迹10 去掉 P15 的 J6自转360°特异点
# A过B败 -> 凶手=自转360°；A败 -> 凶手=8->9接缝本身。
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
j8, j9, j10 = (load_raw((BASE + r"\连续轨迹%s.json") % k) for k in ("8", "9", "10"))

# A: 8 + 9 原样拼接，去掉 9 开头与 8 终点重复的点
dup = 0
while dup < len(j9) and dup < len(j8):
    a, b = j8[-1 - 0] if dup == 0 else None, None
    break
# 9 的 P1 与 8 的 P10 数值相同（-0.0 vs 0.0 视为相等）
def same(p, q, tol=1e-6):
    return all(abs(float(x) - float(y)) <= tol for x, y in zip(p["values"], q["values"]))
skip = 0
for k in range(len(j9)):
    if same(j8[-1], j9[k]):
        skip = k + 1
    else:
        break
VAR_A = to_recs(j8 + j9[skip:])

# B: 10 去掉 spin360 特异点（保留其余原样）
VAR_B = to_recs([it for it in j10 if not (it.get("singular") and it.get("spin360"))])

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
    except Exception as exc:
        cnt = Counter()
        for s in lines:
            m = re.match(r"候选分支未通过：P(\d+)", s)
            if m:
                cnt[int(m.group(1))] += 1
        print("== [%s] 结果: FAIL  %.1fs ==" % (tag, time.time() - t0), flush=True)
        print("   最终错误: %s" % str(exc)[:200], flush=True)
        print("   死点分布(展P:次数): %s" % dict(sorted(cnt.items())), flush=True)
    finally:
        robot.setJoints(PARKED)

try:
    print("变体A拼接后原始点数: %d (跳过9开头重复%d点)" % (len(VAR_A), skip), flush=True)
    print("变体B原始点数: %d (10去掉spin360后)" % len(VAR_B), flush=True)
    run_one("A: 8+9拼接", VAR_A)
    print("", flush=True)
    run_one("B: 10去自转", VAR_B)
finally:
    robot.setJoints(PARKED)
    print("== 判别实验结束，已还原停放关节 ==", flush=True)
