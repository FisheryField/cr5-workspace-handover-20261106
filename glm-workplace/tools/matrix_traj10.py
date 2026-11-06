#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 对照矩阵：从不同起始位姿分别规划 轨迹8 / 轨迹10，分离“起点依赖”与“轨迹内容”两种失败原因。
# 规划器 finally 会还原关节；脚本结束时再次显式还原到初始快照。不移动真实机械臂。
import sys, io, json, ast, math, time, re
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")

SRC = r"D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py"
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
SNAP = robot.Joints().list()[:6]

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
TRAJ = {"8": load(BASE + r"\连续轨迹8.json"), "10": load(BASE + r"\连续轨迹10.json")}

def ik_of(x, y, z, rx, ry, rz):
    t = ns["fanuc_values_to_pose"](x, y, z, rx, ry, rz)
    j = ns["robot"].SolveIK(ns["_tcp_target_to_flange"](t))
    return j.list()[:6] if j else None

STARTS = {
    "S1当前(-600,0,300)": SNAP[:],
    "S3=P1(500,0,300)": ik_of(500, 0, 300, 180, 0, 0),
    "S2=8终点(30,-755)": ik_of(30, -755, 300, 90, 0, 90),
}
for k, v in STARTS.items():
    print(k, "->", ["%.2f" % x for x in v] if v else "IK无解!")

def run(tag, traj, start):
    robot.setJoints(start)
    t0 = time.time()
    lines = []
    def log(m, _lines=lines):
        s = str(m)
        if "候选分支未通过" in s:
            _lines.append(s)
    records = ns["_retreat_orientation_records"](traj)
    try:
        plan = ns["_plan_continuous_trajectory"](records, 500.0, log)
        verdict = "PASS (%d步, %.1fs)" % (len(plan), time.time() - t0)
    except Exception as exc:
        verdict = "FAIL (%.1fs) %s: %s" % (time.time() - t0, type(exc).__name__, str(exc)[:120])
    cnt = Counter()
    for s in lines:
        m = re.match(r"候选分支未通过：P(\d+)", s)
        if m:
            cnt[int(m.group(1))] += 1
    print("\n[%s] %s" % (tag, verdict))
    print("   分支死点分布(展P:次数):", dict(sorted(cnt.items())) or "无")

try:
    for sname, sq in STARTS.items():
        if sq is None:
            continue
        for tname in ("8", "10"):
            run("%s + 轨迹%s" % (sname, tname), TRAJ[tname], sq)
finally:
    robot.setJoints(SNAP)
    print("\n已还原关节:", ["%.3f" % v for v in robot.Joints().list()[:6]])
