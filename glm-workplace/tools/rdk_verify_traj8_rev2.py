#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Verify rev2 (retreat + direct MoveJ bridge) through the patched copy's
# preflight. On failure, also print the failure-point histogram and frontier.
import sys, io, ast, json, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

COPY = r"D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py"
TRJ = r"D:\mydata\glm-workplace\sim_scripts\连续轨迹8_rev2.json"

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
ns = {"__name__": "rev2"}
exec(compile("\n".join(ast.unparse(p) for p in parts), COPY, "exec"), ns)
RDK, robot = ns["RDK"], ns["robot"]
HOME = [-163.62, -0.936, -91.282, 2.218, 90.0, 106.38]
robot.setJoints(HOME)   # NEVER trust station state as the seed
home = robot.Joints().list()[:6]
assert all(abs(a - b) < .01 for a, b in zip(home, HOME)), home

print("connected gate:", robot.ConnectedState())
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

hist = {}
def log(text):
    m = re.match(r"候选分支未通过：P(\d+)：", text)
    if m:
        p = int(m.group(1)); hist[p] = hist.get(p, 0) + 1
    print("  [log]", text)

t0 = time.time()
try:
    plan = ns["_plan_continuous_trajectory"](expanded, 500.0, log)
    print("PREFLIGHT PASSED: %d steps in %.1fs" % (len(plan), time.time() - t0))
    for k, s in enumerate(plan, 1):
        print("  step %2d: %-5s j6=%+.1f special=%s fallback=%s rewinds=%d" % (
            k, s["method"], s["joints"][5], s["special"], s["fallback"], len(s["rewinds"])))
except Exception as exc:
    print("PREFLIGHT FAILED after %.1fs" % (time.time() - t0))
    print("EXACT ERROR the GUI would show:")
    print("  ✕ 连续运动停止：已完成0点，阶段=路径预检；%s: %s" % (type(exc).__name__, exc))
    if hist:
        print("failure histogram (expanded pts):")
        for p in sorted(hist):
            print("  P%-3d x%d" % (p, hist[p]))
        print("FRONTIER = P%d" % max(hist))

robot.setJoints(home)
print("restored joints:", [round(v, 3) for v in robot.Joints().list()[:6]], " items:", len(RDK.ItemList()))
