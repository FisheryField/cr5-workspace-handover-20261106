#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Final: normalize the collision map to the copy-script's standard state
# (obstacles ON, base<->table OFF), confirm final wheel placement, no saves.
import sys, io, ast
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")

COPY = r"D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py"
tree = ast.parse(open(COPY, encoding="utf-8").read())
KEEP = {"_plan_cache", "SIM_SPEED", "MOVEJ_FALLBACK_MAX_DEVIATION_MM", "RDK", "robot"}
parts = []
for node in tree.body:
    if isinstance(node, ast.FunctionDef) or (isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("robodk")) \
       or (isinstance(node, ast.Import) and all(a.name in ("math","itertools","json","threading") for a in node.names)) \
       or (isinstance(node, ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in KEEP) \
       or isinstance(node, ast.If):
        parts.append(node)
ns = {"__name__": "finalize"}
exec(compile("\n".join(ast.unparse(p) for p in parts), COPY, "exec"), ns)
RDK, robot = ns["RDK"], ns["robot"]
from robodk.robolink import ITEM_TYPE_OBJECT, ITEM_TYPE_TOOL

ns["_enable_obstacle_checks"]()

w = RDK.Item('磨砂圆柱_R180_H40', ITEM_TYPE_OBJECT)
table = RDK.Item('安装台_650x650x80mm', ITEM_TYPE_OBJECT)
tool = RDK.Item('门把手_bs1', ITEM_TYPE_TOOL)
B = robot.Parent().PoseAbs()

print("robot<->table at rest now:", RDK.Collision(robot, table), "(0 expected: base pair OFF)")
q = robot.Joints().list()[:6]
print("joints (never moved):", ["%.3f" % v for v in q])
inb = B.inv() * w.PoseAbs()
print("FINAL wheel in-base frame: (%.2f, %.2f, %.2f)" % tuple(v for v in inb.Pos()[:3]))
print("FINAL wheel parent:", w.Parent().Name())
print("collision map: standardized (station still NOT saved)")
