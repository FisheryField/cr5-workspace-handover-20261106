#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Diag2: (A) where did the +179.665 go (rel-parent pose vs GeometryPose)?
# (B) forced-penetration test: does this instance's collision engine respond
#     to tool<->wheel at all? (temp +100mm base-Y push, then restore)
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
ns = {"__name__": "diag2"}
exec(compile("\n".join(ast.unparse(p) for p in parts), COPY, "exec"), ns)
RDK, robot = ns["RDK"], ns["robot"]
from robodk.robolink import ITEM_TYPE_OBJECT, ITEM_TYPE_TOOL, COLLISION_ON, COLLISION_OFF
from robodk.robomath import transl

w = RDK.Item('磨砂圆柱_R180_H40', ITEM_TYPE_OBJECT)
tool = RDK.Item('门把手_bs1', ITEM_TYPE_TOOL)
B = robot.Parent().PoseAbs()
q = robot.Joints().list()[:6]

def show(tag):
    rel = w.PoseAbs()          # world (parent chain applied)
    gp = w.GeometryPose()
    rib = B.inv() * w.PoseAbs()
    print("%s: in-base(%7.2f,%8.2f,%7.2f)  GeometryPose(%7.2f,%7.2f,%7.2f)"
          % (tag, *(v for v in rib.Pos()), *(v for v in gp.Pos())))

show("A. now           ")

# full map ON
ns["_enable_obstacle_checks"]()
print("full map ON, Collisions() at parked pose:", RDK.Collisions())

# B. forced deep penetration: push wheel +100mm along base +Y
wp = w.PoseAbs()
w.setPoseAbs(B * transl(0, 100, 0) * B.inv() * wp)
show("B. pushed +100 Y ")
n_push = RDK.Collisions()
print("Collisions() with +100 push:", n_push)
r = robot.MoveJ_Test(q, q, minstep_deg=1)
print("MoveJ_Test(q,q) with +100 push:", r)
robot.setJoints(q)

# restore
w.setPoseAbs(B * transl(179.665, 0, 0) * B.inv() * B * (wp * (B.inv() * wp).inv() * (B * transl(0, 0, 0) * B.inv() * wp).inv()))
# -- the line above is convoluted; do it cleanly instead:
w.setPoseAbs(wp)   # wp was captured BEFORE the push (i.e., the 179.665 state)
show("C. restored      ")
print("Collisions() restored:", RDK.Collisions())
