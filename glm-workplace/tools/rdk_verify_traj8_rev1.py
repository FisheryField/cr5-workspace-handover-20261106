#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Verify rev1 through the patched copy's own preflight, then restore state.
# Only planning checks run (MoveJ_Test/MoveL_Test); no trajectory motion executes.
import sys, io, ast, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

COPY = r"D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py"
TRJ = r"D:\mydata\glm-workplace\sim_scripts\连续轨迹8_rev1.json"

src = open(COPY, encoding="utf-8").read()
tree = ast.parse(src)
KEEP_ASSIGN = {"_plan_cache", "SIM_SPEED", "MOVEJ_FALLBACK_MAX_DEVIATION_MM", "RDK", "robot"}
parts = []
for node in tree.body:
    if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("robodk"):
        parts.append(node)
    elif isinstance(node, ast.Import):
        if all(a.name in ("math", "itertools", "json", "threading") for a in node.names):
            parts.append(node)
    elif isinstance(node, ast.FunctionDef):
        parts.append(node)
    elif isinstance(node, ast.Assign):
        t = node.targets
        if len(t) == 1 and isinstance(t[0], ast.Name) and t[0].id in KEEP_ASSIGN:
            parts.append(node)
    elif isinstance(node, ast.If):
        parts.append(node)
newsrc = "\n".join(ast.unparse(p) for p in parts)
ns = {"__name__": "traj8_rev1"}
exec(compile(newsrc, COPY, "exec"), ns)
RDK, robot = ns["RDK"], ns["robot"]

st = robot.ConnectedState()
print("connected gate:", st)
home = robot.Joints().list()[:6]
print("start joints:", [round(v, 3) for v in home])

data = json.load(open(TRJ, encoding="utf-8"))
records = []
for item in data:
    is_sing = bool(item.get("singular", False)) and item["type"] == "TCP"
    records.append({
        "type": item["type"], "values": item["values"][:],
        "target": ns["fanuc_values_to_pose"](*item["values"]) if item["type"] == "TCP" else None,
        "joints": None, "singular": is_sing,
        "j6_delta": int(item.get("j6_delta", 180)) if is_sing else 0,
    })
expanded = ns["_retreat_orientation_records"](records)
print("raw %d pts -> expanded %d exec pts" % (len(records), len(expanded)))
for r in expanded:
    print("  %-14s %s" % (r.get("label", "?"), r["values"]))

def log(text):
    print("  [log]", text)

t0 = time.time()
try:
    plan = ns["_plan_continuous_trajectory"](expanded, 500.0, log)
    print("PREFLIGHT PASSED: %d steps in %.1fs" % (len(plan), time.time() - t0))
    for k, s in enumerate(plan, 1):
        print("  step %d: %s special=%s fallback=%s rewinds=%s j6=%+.1f" % (
            k, s["method"], s["special"], s["fallback"], len(s["rewinds"]), s["joints"][5]))
except Exception as exc:
    print("PREFLIGHT FAILED after %.1fs" % (time.time() - t0))
    print("EXACT ERROR the GUI would show:")
    print("  ✕ 连续运动停止：已完成0点，阶段=路径预检；%s: %s" % (type(exc).__name__, exc))

robot.setJoints(home)
print("restored joints:", [round(v, 3) for v in robot.Joints().list()[:6]], " items:", len(RDK.ItemList()))
