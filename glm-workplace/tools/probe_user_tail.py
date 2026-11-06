#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Probe: user's proposed tail -- retreat (0,-750,300,180,0,180) keeping the old
# orientation, then FINAL point (0,-762,300,-90,0,-90) ON the working line with
# the new orientation, then the usual departure (-500,0,300,180,0,0).
# Checks: (1) orientation deltas, (2) static IK x collision of the final point,
# (3) bridge A: retreat -> final, (4) bridge B: final -> departure.
import sys, io, ast, math
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
ns = {"__name__": "probe_user"}
exec(compile("\n".join(ast.unparse(p) for p in parts), COPY, "exec"), ns)
RDK, robot = ns["RDK"], ns["robot"]
robolink = __import__("robodk.robolink", fromlist=["ITEM_TYPE_TOOL", "COLLISION_ON", "COLLISION_OFF"])
from robodk.robomath import pose_angle, invH, transl, norm

ns["_enable_obstacle_checks"]()
HOME = [-163.62, -0.936, -91.282, 2.218, 90.0, 106.38]
robot.setJoints(HOME)   # NEVER trust station state as the seed
home = robot.Joints().list()[:6]
assert all(abs(a - b) < .01 for a, b in zip(home, HOME)), home
lower, upper, _ = robot.JointLimits(); lower, upper = lower.list(), upper.list()
f2p = ns["fanuc_values_to_pose"]

def ang(a, b):
    return math.degrees(pose_angle(invH(f2p(*a)) * f2p(*b)))

P10   = (0, -762, 300, 180, 0, 180)
RET   = (0, -750, 300, 180, 0, 180)
FINAL = (0, -762, 300, -90, 0, -90)
DEP   = (-500, 0, 300, 180, 0, 0)
print("=== orientation deltas (deg) ===")
print("  P10 -> retreat : %.2f (pure retract, expect 0)" % ang(P10, RET))
print("  retreat -> final: %.2f  (the reorientation)" % ang(RET, FINAL))
print("  final -> depart : %.2f  (flip during swing-out)" % ang(FINAL, DEP))

def sols_ok(vals):
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

print("\n=== static IK x collision (wheel ON) ===")
ret_sols = sols_ok(RET)
fin_sols = sols_ok(FINAL)
dep_sols = sols_ok(DEP)
print("  retreat %s : %d sols" % (RET[3:], len(ret_sols)))
print("  final  %s : %d sols" % (FINAL[3:], len(fin_sols)))
for q in fin_sols:
    print("      final sol:", ["%.1f" % v for v in q])
print("  depart %s : %d sols" % (DEP[3:], len(dep_sols)))

print("\n=== bridge A: retreat -> final (wheel ON) ===")
feasA = []
for i, qa in enumerate(ret_sols):
    for j, qb in enumerate(fin_sols):
        if robot.MoveJ_Test(qa, qb, minstep_deg=1) == 0:
            d = max_deviation(qa, qb)
            feasA.append((i, j, d))
            print("  FEASIBLE ret#%d -> fin#%d  dev=%.1f mm  joints=%s" % (i, j, d, ["%.1f" % v for v in qb]))
print("  feasible: %d / %d" % (len(feasA), len(ret_sols) * len(fin_sols)))

print("\n=== bridge B: final -> departure (wheel ON) ===")
feasB = []
for i, qa in enumerate(fin_sols):
    for j, qb in enumerate(dep_sols):
        if robot.MoveJ_Test(qa, qb, minstep_deg=1) == 0:
            d = max_deviation(qa, qb)
            feasB.append((i, j, d))
            print("  FEASIBLE fin#%d -> dep#%d  dev=%.1f mm" % (i, j, d))
print("  feasible: %d / %d" % (len(feasB), len(fin_sols) * len(dep_sols)))

if not feasA or not feasB:
    print("\n=== diagnosis of failing bridge (wheel OFF classification) ===")
    wheel = RDK.Item("磨砂圆柱_R180_H40")
    def wheel_pairs(state):
        for t in RDK.ItemList(robolink.ITEM_TYPE_TOOL):
            p = t.Parent()
            while p.Valid() and p.item != robot.item:
                p = p.Parent()
            if p.Valid():
                RDK.setCollisionActivePair(state, t, wheel)
    A, B, tag = (ret_sols, fin_sols, "A") if not feasA else (fin_sols, dep_sols, "B")
    shown = 0
    for i, qa in enumerate(A):
        for j, qb in enumerate(B):
            if robot.MoveJ_Test(qa, qb, minstep_deg=1) != 0:
                wheel_pairs(robolink.COLLISION_OFF)
                r_off = robot.MoveJ_Test(qa, qb, minstep_deg=1)
                wheel_pairs(robolink.COLLISION_ON)
                d = max_deviation(qa, qb)
                cls = "wheel-collision" if r_off == 0 else ("dev>500" if d > 500 else "other-collision")
                print("  bridge %s %d->%d : %s (dev=%.0f)" % (tag, i, j, cls, d))
                shown += 1
                if shown >= 12:
                    break
        if shown >= 12:
            break

robot.setJoints(home)
print("\nrestored:", ["%.2f" % v for v in robot.Joints().list()[:6]])
