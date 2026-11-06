#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Reproduce the "轨迹8" failure headlessly: extract the patched copy's functions
# verbatim (ast), feed 连续轨迹8.json through the same import->expand->preflight
# path the GUI uses, and print the exact error text. No motion is executed;
# planning only does simulated MoveJ_Test/MoveL_Test. Station file not saved.
import sys, io, ast, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

COPY = r"D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py"
TRJ = r"D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹8.json"

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
        parts.append(node)  # 'if not robot.Valid(): raise' guard
newsrc = "\n".join(ast.unparse(p) for p in parts)
ns = {"__name__": "traj8_repro"}
exec(compile(newsrc, COPY, "exec"), ns)
RDK, robot = ns["RDK"], ns["robot"]
print("connected gate:", robot.ConnectedState())

tool = robot.getLink(__import__("robodk.robolink", fromlist=["ITEM_TYPE_TOOL"]).ITEM_TYPE_TOOL)
print("active tool:", tool.Name(), "PoseTool:", [round(v, 3) for v in tool.PoseTool().Pos()])

# import trajectory exactly like import_trajectory() does
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
    print("  %-14s %s %s" % (r.get("label", "?"), r["type"], r["values"]))

home = robot.Joints().list()[:6]
print("start joints:", [round(v, 3) for v in home])

def log(text):
    print("  [log]", text)

t0 = time.time()
try:
    plan = ns["_plan_continuous_trajectory"](expanded, 500.0, log)
    print("PREFLIGHT PASSED: %d steps in %.1fs" % (len(plan), time.time() - t0))
except Exception as exc:
    print("PREFLIGHT FAILED after %.1fs" % (time.time() - t0))
    print("EXACT ERROR the GUI would show:")
    print("  ✕ 连续运动停止：已完成0点，阶段=路径预检；%s: %s" % (type(exc).__name__, exc))

# Diagnostic variant: same planner but tool-wheel pair OFF (OLD pre-patch behaviour)
robolink = __import__("robodk.robolink", fromlist=["COLLISION_ON", "COLLISION_OFF"])
wheel = RDK.Item("磨砂圆柱_R180_H40")
orig_eoc = ns["_enable_obstacle_checks"]
def eoc_old_behaviour():
    orig_eoc()
    for t in RDK.ItemList(robolink.ITEM_TYPE_TOOL):
        p = t.Parent()
        while p.Valid() and p.item != robot.item:
            p = p.Parent()
        if p.Valid():
            RDK.setCollisionActivePair(robolink.COLLISION_OFF, t, wheel)
ns["_enable_obstacle_checks"] = eoc_old_behaviour
print("\n--- diagnostic: wheel pair OFF (old behaviour), plan again ---")
t1 = time.time()
try:
    plan2 = ns["_plan_continuous_trajectory"](expanded, 500.0, log)
    print("OLD-BEHAVIOUR PLAN: PASSED %d steps in %.1fs (i.e. patch is the only blocker)" % (len(plan2), time.time() - t1))
except Exception as exc:
    print("OLD-BEHAVIOUR PLAN: FAILED in %.1fs -> other blocker exists:" % (time.time() - t1))
    print("  %s: %s" % (type(exc).__name__, exc))

# cleanup: restore wheel pairs OFF, joints home
for t in RDK.ItemList(robolink.ITEM_TYPE_TOOL):
    p = t.Parent()
    while p.Valid() and p.item != robot.item:
        p = p.Parent()
    if p.Valid():
        RDK.setCollisionActivePair(robolink.COLLISION_OFF, t, wheel)
robot.setJoints(home)
print("\nrestored joints:", [round(v, 3) for v in robot.Joints().list()[:6]], " items:", len(RDK.ItemList()))
