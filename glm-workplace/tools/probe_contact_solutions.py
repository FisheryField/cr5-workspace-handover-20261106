#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Contact-solution probe: orientation fixed (-90,0,-90).
# Candidate TCP on offset circle: py = -956 + (180+107.78-d) cos(phi),
#                                 pz =  300 + (180+107.78-d) sin(phi),
# px in {-12,-6,0,6,12,18}  (bar x-span px+[-7.93,0] inside slab +-20).
# Classification per IK solution q:
#   A: all obstacle pairs ON except tool<->wheel  -> MoveJ_Test(q,q) must be 0 (clean)
#   B: only tool<->wheel ON                        -> MoveJ_Test(q,q) must be 1 (contact)
# User's manual arm pose is saved first and RESTORED at the end (never HOME seed).
import sys, io, ast, math, json, time
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
ns = {"__name__": "contactprobe"}
exec(compile("\n".join(ast.unparse(p) for p in parts), COPY, "exec"), ns)
RDK, robot = ns["RDK"], ns["robot"]
from robodk.robolink import ITEM_TYPE_OBJECT, ITEM_TYPE_TOOL, COLLISION_ON, COLLISION_OFF
f2p = ns["fanuc_values_to_pose"]

USER_JOINTS = robot.Joints().list()[:6]          # save user's manual pose
print("user pose saved:", ["%.3f" % v for v in USER_JOINTS])

OBSTACLES = ['安装台_650x650x80mm', '地面_禁止穿越', '磨砂圆柱_R180_H40']
def item(nm): return RDK.Item(nm, ITEM_TYPE_OBJECT)
obs = {nm: item(nm) for nm in OBSTACLES}
for nm, o in obs.items():
    if not o.Valid():
        raise RuntimeError("missing obstacle " + nm)
tool = RDK.Item('门把手_bs1', ITEM_TYPE_TOOL)
robot_links = lambda: None

def pairs_clean_mode():
    """All checks ON except tool<->wheel: arm/table/floor/wheel + tool/table/floor + self."""
    ns["_enable_obstacle_checks"]()
    if RDK.setCollisionActivePair(COLLISION_OFF, tool, obs['磨砂圆柱_R180_H40']) != 1:
        raise RuntimeError("cannot disable tool-wheel pair")

def pairs_contact_mode():
    """Only tool<->wheel ON."""
    RDK.setCollisionActive(COLLISION_OFF)
    if RDK.setCollisionActivePair(COLLISION_ON, tool, obs['磨砂圆柱_R180_H40']) != 1:
        raise RuntimeError("cannot enable tool-wheel pair")

lower, upper, _ = robot.JointLimits(); lower, upper = lower.list(), upper.list()

def ik_sols(tcp):
    allsol = robot.SolveIK_All(ns["_tcp_target_to_flange"](f2p(*tcp, -90, 0, -90)))
    out = []
    for k in range(allsol.size(1)):
        q = allsol[:6, k].list()
        if all(lower[j] <= q[j] <= upper[j] for j in range(6)):
            out.append(q)
    return out

R180 = 180.0; TIP = 107.78
results = []
t0 = time.time()
phis = [0, 10, -10, 20, -20, 30, -30, 45, -45, 60, -60, 75, -75, 90, -90]
xs = [-12, -6, 0, 6, 12, 18]
DELTA = 2.0
for phi in phis:
    rad = math.radians(phi)
    py = -956 + (R180 + TIP - DELTA) * math.cos(rad)
    pz = 300 + (R180 + TIP - DELTA) * math.sin(rad)
    for px in xs:
        tcp = (px, py, pz)
        sols = ik_sols(tcp)
        if not sols:
            results.append(dict(x=px, phi=phi, y=round(py,2), z=round(pz,2), ik=0,
                                ok=0, other_col=None, note="no IK"))
            continue
        pairs_clean_mode()
        clean = [q for q in sols if robot.MoveJ_Test(q, q, minstep_deg=1) == 0]
        note = ""
        if not clean:
            results.append(dict(x=px, phi=phi, y=round(py,2), z=round(pz,2), ik=len(sols),
                                ok=0, other_col=len(sols), note="all sols collide (non-tool)"))
            continue
        pairs_contact_mode()
        ok = [q for q in clean if robot.MoveJ_Test(q, q, minstep_deg=1) != 0]
        if ok:
            note = "CONTACT-ONLY"
        else:
            note = "no contact registered (delta too small?)"
        results.append(dict(x=px, phi=phi, y=round(py,2), z=round(pz,2), ik=len(sols),
                            ok=len(ok), other_col=0, note=note))
    # progress line per phi
    d = [r for r in results if r["phi"] == phi]
    print("phi=%4d: ik>0 %d/%d, contact-only %d  (%.0fs)" %
          (phi, sum(1 for r in d if r["ik"] > 0), len(d),
           sum(1 for r in d if r["note"] == "CONTACT-ONLY"), time.time() - t0))

json.dump(results, open(r"D:\mydata\glm-workplace\tools\contact_results.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("\n=== contact-only solutions (delta=2mm) ===")
for r in results:
    if r["note"] == "CONTACT-ONLY":
        print("  TCP(%6.2f, %8.2f, %7.2f)  phi=%4d  IK=%d OK=%d"
              % (r["x"], r["y"], r["z"], r["phi"], r["ik"], r["ok"]))

robot.setJoints(USER_JOINTS)
print("\nuser pose restored:", ["%.3f" % v for v in robot.Joints().list()[:6]])
