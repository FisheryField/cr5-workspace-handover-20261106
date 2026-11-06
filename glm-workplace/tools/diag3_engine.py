#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Diag3 (read-only for the station): why does the collision engine ignore the
# wheel in this fresh station?
#  A) do tool & wheel items carry real geometry? -> export STL, compare sizes
#  B) does ANY collision fire in this station? -> temp-push wheel to engulf
#     the arm links, count Collisions(), exact-restore, count again
#  C) what tools/objects exist (names+types), which tool is on the robot?
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")
from robodk.robolink import *
from robodk.robomath import transl

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
w = RDK.Item('磨砂圆柱_R180_H40', ITEM_TYPE_OBJECT)
B = robot.Parent().PoseAbs()

print("--- C) items by type ---")
for ty, label in [(ITEM_TYPE_STATION,'station'), (ITEM_TYPE_ROBOT,'robot'),
                  (ITEM_TYPE_TOOL,'tool'), (ITEM_TYPE_OBJECT,'object'),
                  (ITEM_TYPE_FRAME,'frame')]:
    names = RDK.ItemList(ty, True)
    print(" %-8s: %s" % (label, names))

tool = RDK.Item('门把手_bs1', ITEM_TYPE_TOOL)
print("\ntool valid:", tool.Valid(), " parent:", tool.Parent().Name() if tool.Valid() else "-")

print("\n--- A) geometry export test ---")
tmpdir = r"D:\mydata\glm-workplace\tools"
for item, tag, ref in [(tool, 'tool_now', 73884), (w, 'wheel_now', 36084)]:
    p = os.path.join(tmpdir, "diag3_%s.stl" % tag)
    try:
        RDK.Save(p, item)
        sz = os.path.getsize(p)
        print(" %-9s STL: %7d B  (section-9 ref %d B)  %s"
              % (tag, sz, ref, "OK same" if abs(sz-ref) < 2000 else "DIFFERENT"))
    except Exception as e:
        print(" %-9s export FAILED: %s" % (tag, e))

print("\n--- B) engine fire test (temp engulf, exact restore) ---")
q = robot.Joints().list()[:6]
saved_world = w.PoseAbs()          # the good (179.665,-956,300) state
inb = B.inv() * saved_world
print("wheel in-base before test: (%.2f, %.2f, %.2f)" % tuple(v for v in inb.Pos()[:3]))

# full obstacle map ON (from the copy script's own initializer)
import ast
COPY = r"D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py"
tree = ast.parse(open(COPY, encoding="utf-8").read())
KEEP = {"_plan_cache", "SIM_SPEED", "MOVEJ_FALLBACK_MAX_DEVIATION_MM", "RDK", "robot"}
parts = []
for node in tree.body:
    if isinstance(node, (ast.FunctionDef,)) or (isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("robodk")) \
       or (isinstance(node, ast.Import) and all(a.name in ("math","itertools","json","threading") for a in node.names)) \
       or (isinstance(node, ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in KEEP) \
       or isinstance(node, ast.If):
        parts.append(node)
ns = {"__name__": "diag3"}
exec(compile("\n".join(ast.unparse(p) for p in parts), COPY, "exec"), ns)
ns["_enable_obstacle_checks"]()
print("obstacle map ON; parked Collisions():", RDK.Collisions())

# engulf: wheel center onto the wrist area, plane covers links
w.setPoseAbs(B * transl(24, -700, 300) * B.inv() * saved_world)
n1 = RDK.Collisions()
r1 = robot.MoveJ_Test(q, q, minstep_deg=1)
print("engulfed at (24,-700,300): Collisions()=%d  MoveJ_Test=%d" % (n1, r1))

# global all-ON fallback
RDK.setCollisionActive(COLLISION_ON)
n2 = RDK.Collisions()
print("global setCollisionActive(ON): Collisions()=%d" % n2)

# exact restore
w.setPoseAbs(saved_world)
RDK.setCollisionActive(COLLISION_ON)
inb2 = B.inv() * w.PoseAbs()
print("restored wheel in-base: (%.2f, %.2f, %.2f); parked Collisions(): %d"
      % (tuple(v for v in inb2.Pos()[:3]) + (RDK.Collisions(),)))
robot.setJoints(q)
