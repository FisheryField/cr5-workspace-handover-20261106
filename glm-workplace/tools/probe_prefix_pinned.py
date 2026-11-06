#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Plan the PREFIX ONLY (P1..P10 + retreat). On success, dump the full joint
# config at the retreat point -- the family the trajectory actually pins.
import sys, io, ast, json, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

COPY = r"D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py"
SRC = r"D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹8.json"

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
ns = {"__name__": "prefix"}
exec(compile("\n".join(ast.unparse(p) for p in parts), COPY, "exec"), ns)
RDK, robot = ns["RDK"], ns["robot"]
HOME = [-163.62, -0.936, -91.282, 2.218, 90.0, 106.38]
robot.setJoints(HOME)
home = robot.Joints().list()[:6]
assert all(abs(a - b) < .01 for a, b in zip(home, HOME)), home
print("start joints:", [round(v, 3) for v in home])

data = json.load(open(SRC, encoding="utf-8"))
retreat = {"type": "TCP", "values": [0.0, -750.0, 300.0, 180.0, 0.0, 180.0], "singular": False, "j6_delta": 0}
raw = data[:10] + [retreat]
records = []
for item in raw:
    is_sing = bool(item.get("singular", False)) and item["type"] == "TCP"
    records.append({
        "type": item["type"], "values": item["values"][:],
        "target": ns["fanuc_values_to_pose"](*item["values"]) if item["type"] == "TCP" else None,
        "joints": None, "singular": is_sing,
        "j6_delta": int(item.get("j6_delta", 180)) if is_sing else 0,
    })
expanded = ns["_retreat_orientation_records"](records)
print("prefix raw %d -> expanded %d pts" % (len(records), len(expanded)))

def log(text):
    print("  [log]", text)

t0 = time.time()
try:
    plan = ns["_plan_continuous_trajectory"](expanded, 500.0, log)
    print("PREFIX PASSED: %d steps in %.1fs" % (len(plan), time.time() - t0))
    print(">>> PINNED CONFIG AT RETREAT (last step joints):")
    print("    ", ["%.3f" % v for v in plan[-1]["joints"][:6]])
    for k, s in enumerate(plan, 1):
        print("  step %2d: %-5s j6=%+.1f joints=%s" % (k, s["method"], s["joints"][5], ["%.1f" % v for v in s["joints"][:6]]))
except Exception as exc:
    print("PREFIX FAILED after %.1fs: %s: %s" % (time.time() - t0, type(exc).__name__, exc))

robot.setJoints(HOME)
print("restored:", [round(v, 3) for v in robot.Joints().list()[:6]])
