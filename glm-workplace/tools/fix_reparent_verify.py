#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# FIX + VERIFY: wheel was parented under "Dobot CR5 Base" (robot attachment ->
# robot/tool never collide with it). Reparent to station root KEEPING world
# pose (setParentStatic), then verify short-end contact at the placed pose.
import sys, io, ast
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")
from robodk.robolink import *
from robodk.robomath import transl

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
w = RDK.Item('磨砂圆柱_R180_H40', ITEM_TYPE_OBJECT)
tool = RDK.Item('门把手_bs1', ITEM_TYPE_TOOL)
table = RDK.Item('安装台_650x650x80mm', ITEM_TYPE_OBJECT)
B = robot.Parent().PoseAbs()
station = RDK.ActiveStation()
q = robot.Joints().list()[:6]
print("parked joints (unchanged):", ["%.3f" % v for v in q])

print("\n--- before ---")
def par(it):
    p = it.Parent()
    return p.Name() if p.Valid() else "(station root)"
print("wheel parent:", par(w), " world:", ["%.2f" % v for v in w.PoseAbs().Pos()])

# keep world pose, reparent to station root
w.setParentStatic(station)
print("\n--- after reparent ---")
print("wheel parent:", par(w), " world:", ["%.2f" % v for v in w.PoseAbs().Pos()])
inb = B.inv() * w.PoseAbs()
print("wheel in robot-base frame: (%.2f, %.2f, %.2f)" % tuple(v for v in inb.Pos()[:3]))

print("\n--- contact verification (parked arm, wheel untouched) ---")
print("T1 Collision(tool,wheel) at placed pose (delta=5mm) = %d  (1=contact)" % RDK.Collision(tool, w))
print("N1 Collision(tool,table) = %d  (0 expected)" % RDK.Collision(tool, table))

saved = w.PoseAbs()
w.setPoseAbs(B * transl(0, 100, 0) * B.inv() * saved)
print("P1 Collision(tool,wheel) deep push +100Y = %d  (1 expected)" % RDK.Collision(tool, w))
w.setPoseAbs(saved)
print("T2 Collision(tool,wheel) after exact restore = %d  (1 expected)" % RDK.Collision(tool, w))

# copy-script's own initializer for the pair map
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
ns = {"__name__": "fixverify"}
exec(compile("\n".join(ast.unparse(p) for p in parts), COPY, "exec"), ns)
ns["_enable_obstacle_checks"]()
RDK.setCollisionActivePair(COLLISION_OFF, tool, w)
r_clean = robot.MoveJ_Test(q, q, minstep_deg=1)
RDK.setCollisionActive(COLLISION_OFF)
RDK.setCollisionActivePair(COLLISION_ON, tool, w)
r_contact = robot.MoveJ_Test(q, q, minstep_deg=1)
print("\nclean-mode   (all pairs except tool-wheel): %s" % ("PASS - no other contact" if r_clean == 0 else "COLLISION %d" % r_clean))
print("contact-mode (only tool-wheel ON)        : %s" % ("CONTACT confirmed" if r_contact != 0 else "no contact"))
robot.setJoints(q)

ns["_enable_obstacle_checks"]()
print("\nmap restored all-ON; wheel world:", ["%.2f" % v for v in w.PoseAbs().Pos()],
      " parent:", par(w))
print("station NOT saved - all changes live in memory only")
