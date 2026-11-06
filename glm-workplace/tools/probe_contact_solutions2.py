#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Contact-solution probe v2 (corrected parametrization).
# Bar geometry (validated): bar occupies base x[px-7.93,px], y[py-107.78,py-95.48],
# z[pz-12.3,pz+12.3]. Wheel slab x[-20,20], disk center (y,z)=(-956,300), R=180.
# Family 1 (rim contact, approach -Y): py = -668.22 - delta (delta=penetration),
#   contact band in pz: |pz +/-. 12.3 - 300| < sqrt(360*delta - delta^2).
# Family 2 (face contact, tip footprint clips disk edge): px inside (15,19),
#   py = -668.22 - m, pz near band sqrt(360m - m^2).
# Classification identical to v1: clean-mode (all but tool-wheel) must pass,
# contact-mode (only tool-wheel) must collide.
import sys, io, math, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, "utf-8", errors="replace")
import ast
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
ns = {"__name__": "cp2"}
exec(compile("\n".join(ast.unparse(p) for p in parts), COPY, "exec"), ns)
RDK, robot = ns["RDK"], ns["robot"]
from robodk.robolink import ITEM_TYPE_OBJECT, ITEM_TYPE_TOOL, COLLISION_ON, COLLISION_OFF
f2p = ns["fanuc_values_to_pose"]

USER = robot.Joints().list()[:6]
print("user pose saved:", ["%.2f" % v for v in USER])

WHEEL = RDK.Item('磨砂圆柱_R180_H40', ITEM_TYPE_OBJECT)
TOOL = RDK.Item('门把手_bs1', ITEM_TYPE_TOOL)

def clean_mode():
    ns["_enable_obstacle_checks"]()
    RDK.setCollisionActivePair(COLLISION_OFF, TOOL, WHEEL)

def contact_mode():
    RDK.setCollisionActive(COLLISION_OFF)
    RDK.setCollisionActivePair(COLLISION_ON, TOOL, WHEEL)

lower, upper, _ = robot.JointLimits(); lower, upper = lower.list(), upper.list()
def ik_sols(px, py, pz):
    allsol = robot.SolveIK_All(ns["_tcp_target_to_flange"](f2p(px, py, pz, -90, 0, -90)))
    out = []
    for k in range(allsol.size(1)):
        q = allsol[:6, k].list()
        if all(lower[j] <= q[j] <= upper[j] for j in range(6)):
            out.append(q)
    return out

def check(px, py, pz):
    sols = ik_sols(px, py, pz)
    if not sols:
        return (0, 0, 0, "no-IK")
    clean_mode()
    clean = [q for q in sols if robot.MoveJ_Test(q, q, minstep_deg=1) == 0]
    if not clean:
        return (len(sols), 0, 0, "arm/table collide")
    contact_mode()
    ok = [q for q in clean if robot.MoveJ_Test(q, q, minstep_deg=1) != 0]
    tag = "CONTACT" if ok else "no-contact(delta too small)"
    return (len(sols), len(clean), len(ok), tag)

results = []
def rec(fam, px, py, pz, r):
    results.append(dict(family=fam, x=round(px,2), y=round(py,2), z=round(pz,2),
                        ik=r[0], clean=r[1], contact=r[2], note=r[3]))

t0 = time.time()
print("\n=== family 1: rim contact, py=-668.22-delta ===")
for delta in (1.0, 2.0, 3.0, 5.0):
    half = math.sqrt(360*delta - delta*delta)   # contact band half-width (corner rule)
    zoffs = sorted({0.0, round(half-3,1), round(-(half-3),1)})
    for zo in zoffs:
        pz = 300 + zo
        py = -668.22 - delta
        for px in (-12, -6, 0, 6, 12, 18, 24):
            r = check(px, py, pz)
            rec(1, px, py, pz, r)
    n_c = sum(1 for x in results if x["family"]==1 and x["note"]=="CONTACT" and abs(x["y"]+668.22+delta)<0.01)
    print("  delta=%.1f (band half %.1f): contact pts %d/%d  (%.0fs)"
          % (delta, half, n_c, 7*len(zoffs), time.time()-t0))

print("\n=== family 2: face contact, px in (15,19), py=-668.22-m ===")
for px in (15.0, 19.0):
    for m in (5.0, 15.0, 40.0):
        half = math.sqrt(360*m - m*m)
        zoffs = sorted({0.0, round(min(half-14, 60),1), round(-min(half-14, 60),1)})
        for zo in zoffs:
            pz = 300 + zo
            py = -668.22 - m
            r = check(px, py, pz)
            rec(2, px, py, pz, r)
        print("  px=%.0f m=%.0f done (%.0fs)" % (px, m, time.time()-t0))

json.dump(results, open(r"D:\mydata\glm-workplace\tools\contact_results_v2.json","w",encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("\n=== ALL contact-only coordinates (short end touches wheel, everything else clean) ===")
print("%-7s %7s %9s %8s  %5s %6s %8s" % ("family","x","y","z","IK","clean","contact"))
for r in results:
    if r["note"] == "CONTACT":
        print("F%d      %7.2f %9.2f %8.2f  %5d %6d %8d" % (r["family"], r["x"], r["y"], r["z"], r["ik"], r["clean"], r["contact"]))

from collections import Counter
print("\nsummary by note:", dict(Counter(r["note"] for r in results)))

robot.setJoints(USER)
print("\nuser pose restored:", ["%.2f" % v for v in robot.Joints().list()[:6]])
