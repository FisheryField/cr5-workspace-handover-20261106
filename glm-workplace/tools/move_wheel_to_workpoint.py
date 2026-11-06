#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Move 磨砂圆柱 in the OPEN (unsaved) station: shift +179.665mm along the
# ROBOT BASE +X axis so the parked arm (flange (24,-673.22,300), Rxyz
# (-90,0,-90)) gets short-end-only work contact (delta=5mm).
# Then verify by collision classification. No joint moves, no station save.
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
ns = {"__name__": "movewheel"}
exec(compile("\n".join(ast.unparse(p) for p in parts), COPY, "exec"), ns)
RDK, robot = ns["RDK"], ns["robot"]
from robodk.robolink import ITEM_TYPE_OBJECT, ITEM_TYPE_TOOL, COLLISION_ON, COLLISION_OFF
from robodk.robomath import transl

w = RDK.Item('磨砂圆柱_R180_H40', ITEM_TYPE_OBJECT)
base = robot.Parent()
tool = RDK.Item('门把手_bs1', ITEM_TYPE_TOOL)

old_world = w.PoseAbs()
B = base.PoseAbs()
old_in_base = B.inv() * old_world
print("wheel in base BEFORE:", ["%.3f" % v for v in old_in_base.Pos()])

DX = 179.665
new_world = B * transl(DX, 0, 0) * B.inv() * old_world
w.setPoseAbs(new_world)

new_in_base = B.inv() * w.PoseAbs()
print("wheel in base AFTER :", ["%.3f" % v for v in new_in_base.Pos()])
print("world pos BEFORE:", ["%.2f" % v for v in old_world.Pos()])
print("world pos AFTER :", ["%.2f" % v for v in w.PoseAbs().Pos()])

# ---------- verification ----------
q = robot.Joints().list()[:6]      # parked arm, do not move
print("parked joints:", ["%.3f" % v for v in q])

def clean_mode():
    ns["_enable_obstacle_checks"]()
    RDK.setCollisionActivePair(COLLISION_OFF, tool, w)

def contact_mode():
    RDK.setCollisionActive(COLLISION_OFF)
    RDK.setCollisionActivePair(COLLISION_ON, tool, w)

clean_mode()
r1 = robot.MoveJ_Test(q, q, minstep_deg=1)
contact_mode()
r2 = robot.MoveJ_Test(q, q, minstep_deg=1)
print("\nclean-mode  (all pairs except tool-wheel): %s" % ("PASS no collision" if r1 == 0 else "COLLISION"))
print("contact-mode(only tool-wheel)           : %s" % ("CONTACT detected" if r2 != 0 else "no contact"))

flange = robot.Pose()
print("flange after tests:", ["%.2f" % v for v in flange.Pos()])
robot.setJoints(q)

# restore station-wide collision map to the fully-armed state
ns["_enable_obstacle_checks"]()
print("collision map restored to all-ON")
print("(station NOT saved - wheel move lives in memory only)")
