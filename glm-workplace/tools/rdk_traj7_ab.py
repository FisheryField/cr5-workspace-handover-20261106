#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Experiment: run Trajectory 7 (the known-good baseline) through the SAME
# patched-copy preflight twice:
#   A = copy behaviour (wheel pair ON after _enable_obstacle_checks)
#   B = original behaviour (wheel pairs forced OFF, i.e. old blind spot)
# No motion executes; joints restored at the end. Station not saved.
import sys, io, ast, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

COPY = r"D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py"
TRJ = r"D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹7.json"

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
ns = {"__name__": "traj7_ab"}
exec(compile(newsrc, COPY, "exec"), ns)
RDK, robot = ns["RDK"], ns["robot"]
robolink = __import__("robodk.robolink", fromlist=["ITEM_TYPE_TOOL", "COLLISION_OFF"])

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

logs = []
def log(text):
    logs.append(text)

def wheel_pairs_off():
    wheel = RDK.Item("磨砂圆柱_R180_H40")
    for t in RDK.ItemList(robolink.ITEM_TYPE_TOOL):
        p = t.Parent()
        while p.Valid() and p.item != robot.item:
            p = p.Parent()
        if p.Valid():
            RDK.setCollisionActivePair(robolink.COLLISION_OFF, t, wheel)

def run(tag):
    logs.clear()
    robot.setJoints(home)
    t0 = time.time()
    try:
        plan = ns["_plan_continuous_trajectory"](expanded, 500.0, log)
        print("[%s] PASSED: %d steps in %.1fs" % (tag, len(plan), time.time() - t0))
        return True
    except Exception as exc:
        print("[%s] FAILED after %.1fs: %s: %s" % (tag, time.time() - t0, type(exc).__name__, exc))
        seen = []
        for line in logs:
            if line.startswith("候选分支未通过") and line not in seen:
                seen.append(line)
        print("  distinct branch failures (%d):" % len(seen))
        for line in seen[:12]:
            print("   -", line[:160])
        return False

# A: copy behaviour (wheel checked)
run("A-copy")
# B: original behaviour (wheel not checked)
wheel_pairs_off()
orig_eoc = ns["_enable_obstacle_checks"]
def eoc_then_off():
    orig_eoc()
    wheel_pairs_off()
ns["_enable_obstacle_checks"] = eoc_then_off
run("B-original")
ns["_enable_obstacle_checks"] = orig_eoc
wheel_pairs_off()
robot.setJoints(home)
print("restored joints:", [round(v, 3) for v in robot.Joints().list()[:6]], " items:", len(RDK.ItemList()))
