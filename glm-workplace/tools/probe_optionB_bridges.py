#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Probe option B tail: retreat (0,-750,180,0,180) -> deepest clean new-orient
# point (30,-756,-90,0,-90) -> departure (-500,0,180,0,0). Bridges with wheel ON.
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
ns = {"__name__": "probeB"}
exec(compile("\n".join(ast.unparse(p) for p in parts), COPY, "exec"), ns)
RDK, robot = ns["RDK"], ns["robot"]
from robodk.robomath import transl, norm

ns["_enable_obstacle_checks"]()
HOME = [-163.62, -0.936, -91.282, 2.218, 90.0, 106.38]
robot.setJoints(HOME)
lower, upper, _ = robot.JointLimits(); lower, upper = lower.list(), upper.list()
f2p = ns["fanuc_values_to_pose"]

def sols(vals):
    allsol = robot.SolveIK_All(ns["_tcp_target_to_flange"](f2p(*vals)))
    out = []
    for k in range(allsol.size(1)):
        q = allsol[:6, k].list()
        if all(lower[j] <= q[j] <= upper[j] for j in range(6)):
            if robot.MoveJ_Test(q, q, minstep_deg=1) == 0:
                out.append(q)
    return out

def max_deviation(qa, qb, n=40):
    off = 159.629
    def tcp(p):
        return (p * transl(0, 0, off)).Pos()
    a, b = tcp(robot.SolveFK(qa)), tcp(robot.SolveFK(qb))
    worst = 0.0
    for s in range(1, n):
        t = s / n
        q = [qa[j] + (qb[j] - qa[j]) * t for j in range(6)]
        pt = tcp(robot.SolveFK(q))
        ab = [b[i] - a[i] for i in range(3)]
        ap = [pt[i] - a[i] for i in range(3)]
        tt = max(0.0, min(1.0, sum(ap[i] * ab[i] for i in range(3)) / (sum(x * x for x in ab) or 1e-9)))
        closest = [a[i] + tt * ab[i] for i in range(3)]
        worst = max(worst, norm([pt[i] - closest[i] for i in range(3)]))
    return worst

def bridge(tag, va, vb):
    A, B = sols(va), sols(vb)
    feas = []
    for i, qa in enumerate(A):
        for j, qb in enumerate(B):
            if robot.MoveJ_Test(qa, qb, minstep_deg=1) == 0:
                feas.append((i, j, max_deviation(qa, qb)))
    print("%s : %d/%d feasible" % (tag, len(feas), len(A) * len(B)))
    for i, j, d in feas[:8]:
        print("    %d->%d dev=%.0fmm" % (i, j, d))
    return feas

RET  = (0, -750, 300, 180, 0, 180)
DEEP = (30, -756, 300, -90, 0, -90)
DEP  = (-500, 0, 300, 180, 0, 0)
fA = bridge("A: retreat -> (30,-756,-90,0,-90)", RET, DEEP)
fB = bridge("B: (30,-756) -> departure (-500,0)", DEEP, DEP)
# chain: any sol index compatible both ways?
if fA and fB:
    ends = {j for _, j, _ in fA}
    starts = {i for i, _, _ in fB}
    print("chained (same sol family at deep point):", sorted(ends & starts) or "none (planner will re-pick via IK)")

robot.setJoints(HOME)
print("\nrestored:", ["%.2f" % v for v in robot.Joints().list()[:6]])
