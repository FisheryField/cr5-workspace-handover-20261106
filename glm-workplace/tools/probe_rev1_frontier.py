#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Probe 1: parse the existing rev1 preflight log -> failure-point histogram
#          + frontier (the furthest point any branch reached).
# Probe 2: static anatomy of the turn pose: IK solutions x static collision.
import sys, io, re, ast
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

LOG = r"D:\mydata\glm-workplace\.zwork\background\2026-09-29T08-06-42-367Z-jxmnj4.log"
COPY = r"D:\mydata\glm-workplace\sim_scripts\机械臂TCP仿真_副本.py"

# ---- Probe 1: histogram from existing log ----
hist = {}
total = 0
for line in open(LOG, encoding="utf-8", errors="replace"):
    m = re.match(r"\s*\[log\] 候选分支未通过：P(\d+)：", line)
    if m:
        p = int(m.group(1)); hist[p] = hist.get(p, 0) + 1; total += 1
print("=== rev1 branch-failure histogram (expanded-point numbers) ===")
for p in sorted(hist):
    print("  P%-3d killed %3d branch(es)" % (p, hist[p]))
print("  total failed branches: %d" % total)
if hist:
    frontier = max(hist)
    print("  FRONTIER = P%d (furthest point any branch reached before dying)" % frontier)

labels = {1:"P1 (500,0)",2:"P2前退让",3:"P2退让位换向(0,-750)",4:"P2 (0,-775)",5:"P3 (100,-775)",
          6:"P4前退让",7:"P4退让位换向",8:"P4返回工作位",9:"P5 (0,-775)",10:"P6前退让",
          11:"P6退让位换向(0,-750)",12:"P6 (0,-762)",13:"P7 (0,-762)",14:"P8 (100,-762)",
          15:"P9 奇异点",16:"P10 (0,-762)",17:"P11 退让12mm",18:"P12 原地换向[插入]",
          19:"P13 (30,-750)",20:"P14 (-500,0)"}
print("  label map:", "; ".join("P%d=%s" % (k, v) for k, v in labels.items() if k in hist))

# ---- Probe 2: static anatomy of turn poses ----
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
ns = {"__name__": "probe2"}
exec(compile("\n".join(ast.unparse(p) for p in parts), COPY, "exec"), ns)
RDK, robot = ns["RDK"], ns["robot"]
f2p = ns["fanuc_values_to_pose"]
home = robot.Joints().list()[:6]
lower, upper, _ = robot.JointLimits(); lower, upper = lower.list(), upper.list()

def rot_eq(a, b):
    from robodk.robomath import pose_angle, invH
    ang = pose_angle(invH(f2p(*a)) * f2p(*b))
    return ang

print("\n=== Euler-representation equivalence checks (angle between poses, deg) ===")
base = (0, -750, 300, 180, 0, 180)
targ = (0, -750, 300, -90, 0, -90)
print("  (180,0,180) vs (-90,0,-90): %.2f" % rot_eq(base, targ))
for cand in [(270, 0, 270), (90, 180, 90)]:
    v = rot_eq(targ, (0, -750, 300) + cand)
    print("  (-90,0,-90) vs %s: %.4f %s" % (cand, v, "<-- EQUIVALENT" if v < .01 else ""))
print("  step angles: base->mid1(180,0,270): %.2f, mid1->mid2: (checked above), mid2->targ: see equiv" %
      rot_eq(base, (0, -750, 300, 180, 0, 270)))

print("\n=== static IK x collision anatomy ===")
def anatomy(tag, vals):
    target = f2p(*vals)
    sols = ns["_tcp_target_to_flange"](target)
    allsol = robot.SolveIK_All(sols)
    n = allsol.size(1)
    ok = []
    for k in range(n):
        q = allsol[:6, k].list()
        if not all(lower[j] <= q[j] <= upper[j] for j in range(6)):
            continue
        if robot.MoveJ_Test(q, q, minstep_deg=1) == 0:
            ok.append(q)
    print("  %-28s IK=%d, in-limit&collision-free=%d" % (tag, n, len(ok)))
    for q in ok[:6]:
        print("      OK sol:", ["%.1f" % v for v in q])

anatomy("from (180,0,180)", base)
anatomy("turn target (-90,0,-90)", targ)
anatomy("mid1 (180,0,270)", (0, -750, 300, 180, 0, 270))
anatomy("mid2 (270,0,270)", (0, -750, 300, 270, 0, 270))
anatomy("orig P11 (30,-750,-90,0,-90)", (30, -750, 300, -90, 0, -90))
robot.setJoints(home)
print("\nrestored:", ["%.2f" % v for v in robot.Joints().list()[:6]])
