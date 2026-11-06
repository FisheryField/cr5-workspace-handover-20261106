#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 无头复现：用副本脚本自己的规划器跑 连续轨迹8/9/10/拼接，抓确切失败原因。
# 用法: python plan_repro_traj10.py [10|8|9|concat]
# 不移动机械臂（规划器 finally 里恢复关节），只读工作站。
import sys, io, json, ast, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")

SRC = r"D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py"
WHICH = sys.argv[1] if len(sys.argv) > 1 else "10"

# ---- AST 前置段提取：只 exec 函数/导入/白名单赋值，跳过 UI 与启动段 ----
tree = ast.parse(open(SRC, encoding="utf-8").read())
KEEP_ASSIGN = {"SIM_SPEED", "ALLOW_SIMULATION", "MOVEJ_FALLBACK_MAX_DEVIATION_MM",
               "_plan_cache", "RDK", "robot", "target_pose", "target_joints",
               "simulation_running", "trajectory_records"}
ns = {}
for node in tree.body:
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        mods = ([a.name for a in node.names] if isinstance(node, ast.Import)
                else [node.module or ""])
        if any(m.split(".")[0] == "tkinter" for m in mods):
            continue  # 本环境无 tkinter，规划函数不依赖它
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                         ast.Import, ast.ImportFrom)):
        ast_module = ast.Module(body=[node], type_ignores=[])
        exec(compile(ast_module, SRC, "exec"), ns)
    elif isinstance(node, ast.Assign) and all(isinstance(t, ast.Name) and t.id in KEEP_ASSIGN for t in node.targets):
        ast_module = ast.Module(body=[node], type_ignores=[])
        exec(compile(ast_module, SRC, "exec"), ns)
ns["math"] = math

RDK, robot = ns["RDK"], ns["robot"]
lo, hi, _ = robot.JointLimits()
lo, hi = lo.list(), hi.list()
print("J limits:", ["[%.0f,%.0f]" % (lo[i], hi[i]) for i in range(6)])
print("start joints:", ["%.3f" % j for j in robot.Joints().list()[:6]])

def load(path):
    data = json.load(open(path, encoding="utf-8"))
    recs = []
    for item in data:
        is_s = bool(item.get("singular", False)) and item["type"] == "TCP"
        is_spin = is_s and bool(item.get("spin360", False))
        raw_d = int(item.get("j6_delta", 360 if is_spin else 180)) if is_s else 0
        recs.append({
            "type": item["type"], "values": item["values"][:],
            "target": ns["fanuc_values_to_pose"](*item["values"]) if item["type"] == "TCP" else None,
            "joints": None, "singular": is_s, "spin360": is_spin,
            "j6_delta": ((360 if is_spin else 180) * (1 if raw_d >= 0 else -1)) if is_s else 0,
        })
    return recs

BASE = r"D:\mydata\working things\dobot_arm\RoboDK files 2"
if WHICH == "concat":
    recs = load(BASE + r"\连续轨迹8.json") + load(BASE + r"\连续轨迹9.json")
else:
    recs = load((BASE + r"\连续轨迹%s.json") % WHICH)

log_lines = []
def log(msg):
    log_lines.append(str(msg))
    print("  |", msg)

records = ns["_retreat_orientation_records"](recs)
print("== %s：%d 原始点 -> %d 执行点 ==" % (WHICH, len(recs), len(records)))
for i, r in enumerate(records, 1):
    v = r["values"]
    print("  展P%-3d 标签=%-10s (%8.2f,%8.2f,%7.1f,%6.1f,%5.1f,%6.1f) sing=%-5s spin=%-5s d=%+4d lin=%s" % (
        i, r.get("label", ""), v[0], v[1], v[2], v[3], v[4], v[5],
        r.get("singular", False), r.get("spin360", False), r.get("j6_delta", 0) or 0,
        r.get("require_linear", False)))
try:
    plan = ns["_plan_continuous_trajectory"](records, 500.0, log)
    print("== PLAN OK: %d steps ==" % len(plan))
    for i, st in enumerate(plan, 1):
        print("  step%-3d %-6s J6=%+9.3f special=%-5s delta=%s rewinds=%d" % (
            i, st["method"], st["joints"][5], st["special"], st["j6_delta"], len(st["rewinds"])))
except Exception as exc:
    print("== PLAN FAIL: %s: %s ==" % (type(exc).__name__, exc))
    print("-- 最后12条日志 --")
    for line in log_lines[-12:]:
        print("  |", line)
print("joints after:", ["%.3f" % j for j in robot.Joints().list()[:6]])
