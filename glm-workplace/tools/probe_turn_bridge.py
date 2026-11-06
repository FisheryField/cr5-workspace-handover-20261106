#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Bridge matrix probe: why does the in-place turn (0,-750) (180,0,180)->(-90,0,-90)
# fail? For every (base_sol -> turn_sol) pair run MoveJ_Test twice (wheel ON / OFF),
# and sample the joint-space path to measure max TCP deviation from the straight
# line (the script's 500mm cap). Classifies: wheel-collision / other-collision /
# deviation / feasible. No motion executes; joints restored.
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
ns = {"__name__": "probe3"}
exec(compile("\n".join(ast.unparse(p) for p in parts), COPY, "exec"), ns)
RDK, robot = ns["RDK"], ns["robot"]
robolink = __import__("robodk.robolink", fromlist=["ITEM_TYPE_TOOL", "COLLISION_ON", "COLLISION_OFF"])
from robodk.robomath import norm

# activate the script's obstacle map first
ns["_enable_obstacle_checks"]()
wheel = RDK.Item("磨砂圆柱_R180_H40")

def wheel_pairs(state):
    for t in RDK.ItemList(robolink.ITEM_TYPE_TOOL):
        p = t.Parent()
        while p.Valid() and p.item != robot.item:
            p = p.Parent()
        if p.Valid():
            RDK.setCollisionActivePair(state, t, wheel)

home = robot.Joints().list()[:6]
lower, upper, _ = robot.JointLimits(); lower, upper = lower.list(), upper.list()
f2p = ns["fanuc_values_to_pose"]

def sols_ok(vals):
    allsol = robot.SolveIK_All(ns["_tcp_target_to_flange"](f2p(*vals)))
    out = []
    for k in range(allsol.size(1)):
        q = allsol[:6, k].list()
        if all(lower[j] <= q[j] <= upper[j] for j in range(6)):
            out.append(q)
    return out

def max_deviation(qa, qb, n=40):
    # sample joint-linear path, TCP vs straight line qa-TCP -> qb-TCP
    pa = robot.SolveFK(qa); pb = robot.SolveFK(qb)
    # TCP = flange * tool offset (tool = flange * [0,0,159.629] since tool axis along flange z)
    off = 159.629
    import robodk.robomath as m
    from robodk.robomath import transl
    def tcp(p):
        return (p * transl(0, 0, off)).Pos()
    a, b = tcp(pa), tcp(pb)
    worst = 0.0
    for s in range(1, n):
        t = s / n
        q = [qa[j] + (qb[j] - qa[j]) * t for j in range(6)]
        pt = tcp(robot.SolveFK(q))
        # distance point->segment(a,b)
        ab = [b[i] - a[i] for i in range(3)]
        ap = [pt[i] - a[i] for i in range(3)]
        tt = max(0.0, min(1.0, sum(ap[i] * ab[i] for i in range(3)) / (sum(x * x for x in ab) or 1e-9)))
        closest = [a[i] + tt * ab[i] for i in range(3)]
        d = norm([pt[i] - closest[i] for i in range(3)])
        worst = max(worst, d)
    return worst

base_sols = sols_ok((0, -750, 300, 180, 0, 180))
turn_sols = sols_ok((0, -750, 300, -90, 0, -90))
far_sols  = sols_ok((30, -750, 300, -90, 0, -90))
print("base sols:", len(base_sols), " turn sols:", len(turn_sols), " far(30,-750) sols:", len(far_sols))

best = None
rows = []
for i, qa in enumerate(base_sols):
    for j, qb in enumerate(turn_sols):
        wheel_pairs(robolink.COLLISION_ON)
        r_on = robot.MoveJ_Test(qa, qb, minstep_deg=1)
        wheel_pairs(robolink.COLLISION_OFF)
        r_off = robot.MoveJ_Test(qa, qb, minstep_deg=1)
        dev = max_deviation(qa, qb)
        jmax = max(abs(b - a) for a, b in zip(qa, qb))
        rows.append((i, j, r_on, r_off, dev, jmax))
wheel_pairs(robolink.COLLISION_ON)

print("\npair: base#i -> turn#j | wheelON | wheelOFF | maxTCPdev(mm) | maxJointSwing(deg)")
for i, j, r_on, r_off, dev, jmax in rows:
    tag = "FEASIBLE!" if r_on == 0 else ("wheel-collision" if r_off == 0 else ("dev>500" if dev > 500 else "other-collision/limits"))
    print("  %2d->%2d  %5d  %5d  %9.1f  %6.1f   %s" % (i, j, r_on, r_off, dev, jmax, tag))

feas = [r for r in rows if r[2] == 0]
mindev_off = min([r[4] for r in rows], default=None)
print("\nfeasible with wheel ON:", len(feas))
print("min deviation among all pairs: %.1f mm (cap 500)" % mindev_off)

# Also: can we reach the far point (30,-750,-90,0,-90) directly from base sols?
print("\n--- bridge to far point (30,-750,-90,0,-90) ---")
cnt = 0
for i, qa in enumerate(base_sols):
    for j, qb in enumerate(far_sols):
        r_on = robot.MoveJ_Test(qa, qb, minstep_deg=1)
        if r_on == 0:
            cnt += 1
            print("  FEASIBLE: base#%d -> far#%d  dev=%.1f" % (i, j, max_deviation(qa, qb)))
print("  feasible pairs:", cnt, "/", len(base_sols) * len(far_sols))

robot.setJoints(home)
print("\nrestored:", ["%.2f" % v for v in robot.Joints().list()[:6]])
