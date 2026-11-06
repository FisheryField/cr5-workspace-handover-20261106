#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Grid scan for orientation (-90,0,-90): x in {0,+30,-30}, y=-762..-748.
# Also sanity-check (30,-750) [orig P11, expect clean] and the trivial bridge
# P10 (0,-762,180,0,180) -> retreat (0,-750,180,0,180).
import sys, io, ast
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

COPY = r"D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py"
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
ns = {"__name__": "scan"}
exec(compile("\n".join(ast.unparse(p) for p in parts), COPY, "exec"), ns)
RDK, robot = ns["RDK"], ns["robot"]

ns["_enable_obstacle_checks"]()
HOME = [-163.62, -0.936, -91.282, 2.218, 90.0, 106.38]
robot.setJoints(HOME)
lower, upper, _ = robot.JointLimits(); lower, upper = lower.list(), upper.list()
f2p = ns["fanuc_values_to_pose"]

def sols(vals):
    allsol = robot.SolveIK_All(ns["_tcp_target_to_flange"](f2p(*vals)))
    ik = allsol.size(1)
    ok = []
    for k in range(ik):
        q = allsol[:6, k].list()
        if all(lower[j] <= q[j] <= upper[j] for j in range(6)):
            if robot.MoveJ_Test(q, q, minstep_deg=1) == 0:
                ok.append(q)
    return ik, ok

print("=== orientation (-90,0,-90) grid: IK / collision-free (wheel ON) ===")
print("  y \\ x |   x=0        x=30        x=-30")
for y in range(-762, -747, 2):
    row = []
    for x in (0, 30, -30):
        ik, ok = sols((x, y, 300, -90, 0, -90))
        row.append("%2d/%-2d" % (ik, len(ok)))
    print("  %d | %8s %11s %11s" % (y, row[0], row[1], row[2]))

print("\n=== sanity: orig P11 (30,-750,-90,0,-90) ===")
ik, ok = sols((30, -750, 300, -90, 0, -90))
print("  IK=%d clean=%d" % (ik, len(ok)))

print("\n=== bridge P10(0,-762,180,0,180) -> retreat(0,-750,180,0,180), wheel ON ===")
ikA, a = sols((0, -762, 300, 180, 0, 180))
ikB, b = sols((0, -750, 300, 180, 0, 180))
feas = 0
for qa in a:
    for qb in b:
        if robot.MoveJ_Test(qa, qb, minstep_deg=1) == 0:
            feas += 1
print("  feasible %d / %d (this is a pure 12mm y-retract MoveL)" % (feas, len(a) * len(b)))

robot.setJoints(HOME)
print("\nrestored:", ["%.2f" % v for v in robot.Joints().list()[:6]])
