#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Diagnose why contact-mode reported no contact after wheel move.
# Read-only queries: pair-map return values, RDK.Collisions() count at the
# parked pose, and the copy script's _collision_details listing.
import sys, io, ast
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")

COPY = r"D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py"
tree = ast.parse(open(COPY, encoding="utf-8").read())
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
ns = {"__name__": "diag"}
exec(compile("\n".join(ast.unparse(p) for p in parts), COPY, "exec"), ns)
RDK, robot = ns["RDK"], ns["robot"]
from robodk.robolink import ITEM_TYPE_OBJECT, ITEM_TYPE_TOOL, COLLISION_ON, COLLISION_OFF

w = RDK.Item('磨砂圆柱_R180_H40', ITEM_TYPE_OBJECT)
tool = RDK.Item('门把手_bs1', ITEM_TYPE_TOOL)
B = robot.Parent().PoseAbs()
wib = B.inv() * w.PoseAbs()
print("wheel in base now:", ["%.3f" % v for v in wib.Pos()])
q = robot.Joints().list()[:6]
print("parked joints    :", ["%.3f" % v for v in q])
flange = robot.Pose()
tcp = flange * robot.PoseTool()
from robodk.robomath import Pose_2_Fanuc
print("TCP (Fanuc)      : [%.2f, %.2f, %.2f]" % tuple(Pose_2_Fanuc(tcp))[:3])

print("\n--- full map ON, count colliding pairs at parked pose ---")
ns["_enable_obstacle_checks"]()
ret_on = RDK.setCollisionActivePair(COLLISION_ON, tool, w)
print("setCollisionActivePair(tool,wheel,ON) returned:", ret_on)
n = RDK.Collisions()
print("RDK.Collisions() =", n, "(number of colliding object pairs now)")
try:
    det = ns["_collision_details"]()
    print("_collision_details:", det)
except Exception as e:
    print("_collision_details err:", type(e).__name__, e)

print("\n--- only tool-wheel pair ON ---")
RDK.setCollisionActive(COLLISION_OFF)
ret2 = RDK.setCollisionActivePair(COLLISION_ON, tool, w)
print("setCollisionActivePair returned:", ret2)
n2 = RDK.Collisions()
print("RDK.Collisions() =", n2)
r = robot.MoveJ_Test(q, q, minstep_deg=1)
print("MoveJ_Test(q,q)  =", r)
robot.setJoints(q)

# restore
ns["_enable_obstacle_checks"]()
print("\nmap restored all-ON; RDK.Collisions() now:", RDK.Collisions())
