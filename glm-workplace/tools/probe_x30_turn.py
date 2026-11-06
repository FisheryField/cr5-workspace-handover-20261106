#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# At x=30 (the only clean zone, wheel disc spans x in [-20,20]):
# chain S0 (30,-750,180,0,180) -> M1 (30,-750,180,0,270) -> M2 (30,-750,270,0,270 = -90,0,-90)
# plus the direct 120-degree hop and the trivial slide from x=0.
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
ns = {"__name__": "x30"}
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

R0  = (0,  -750, 300, 180, 0, 180)   # retreat (pinned family arrives here)
S0  = (30, -750, 300, 180, 0, 180)   # slide (pure MoveL target)
M1  = (30, -750, 300, 180, 0, 270)   # hop 1 (90 deg)
M2  = (30, -750, 300, 270, 0, 270)   # hop 2 (90 deg) == (-90,0,-90) exactly
DEP = (-500, 0, 300, 180, 0, 0)

sets = {"R0": sols(R0), "S0": sols(S0), "M1": sols(M1), "M2": sols(M2), "DEP": sols(DEP)}
for k, v in sets.items():
    print("%-4s %s : %d clean sols" % (k, (k == "R0" and R0 or k == "S0" and S0 or k == "M1" and M1 or k == "M2" and M2 or DEP)[3:], len(v)))

def matrix(a_name, b_name):
    A, B = sets[a_name], sets[b_name]
    feas = []
    for i, qa in enumerate(A):
        for j, qb in enumerate(B):
            if robot.MoveJ_Test(qa, qb, minstep_deg=1) == 0:
                feas.append((i, j, max_deviation(qa, qb)))
    print("\n%s -> %s : %d/%d feasible" % (a_name, b_name, len(feas), len(A) * len(B)))
    for i, j, d in feas:
        print("    %d->%d dev=%.0fmm  B-sol=%s" % (i, j, d, ["%.0f" % v for v in B[j]]))
    return feas

f_slide = matrix("R0", "S0")   # pure 30mm MoveL: many expected
f_h1    = matrix("S0", "M1")
f_h2    = matrix("M1", "M2")
f_dir   = matrix("S0", "M2")   # direct 120 deg at x=30
f_dep   = matrix("M2", "DEP")  # exit from new orientation

# chained 2-hop viability per S0 family
if f_h1 and f_h2:
    h1_by_i = {}
    for i, j, d in f_h1:
        h1_by_i.setdefault(i, set()).add(j)
    h2_by_i = {i for i, _, _ in f_h2}
    print("\n2-hop chains: S0 families with full chain:", sorted(i for i, js in h1_by_i.items() if js & h2_by_i))

robot.setJoints(HOME)
print("\nrestored:", ["%.2f" % v for v in robot.Joints().list()[:6]])
