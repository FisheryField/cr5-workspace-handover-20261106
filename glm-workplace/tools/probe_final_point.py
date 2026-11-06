#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Dissect the user's final point (0,-762,300,-90,0,-90): raw IK count, why each
# solution dies (limit / wheel / other), and where the handle axis actually
# points vs the old orientation. Also scan y=-762..-750 to find the shallowest
# depth where the new orientation becomes statically clean.
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
ns = {"__name__": "probe_final"}
exec(compile("\n".join(ast.unparse(p) for p in parts), COPY, "exec"), ns)
RDK, robot = ns["RDK"], ns["robot"]
robolink = __import__("robodk.robolink", fromlist=["ITEM_TYPE_TOOL", "COLLISION_ON", "COLLISION_OFF"])
from robodk.robomath import transl

ns["_enable_obstacle_checks"]()
HOME = [-163.62, -0.936, -91.282, 2.218, 90.0, 106.38]
robot.setJoints(HOME)
lower, upper, _ = robot.JointLimits(); lower, upper = lower.list(), upper.list()
f2p = ns["fanuc_values_to_pose"]

def dissect(vals, wheel):
    target = ns["_tcp_target_to_flange"](f2p(*vals))
    allsol = robot.SolveIK_All(target)
    n = allsol.size(1)
    stats = {"ik": n, "limit": 0, "wheel": 0, "other": 0, "ok": 0}
    okq = None
    wheel_item = RDK.Item("磨砂圆柱_R180_H40")
    def wheel_pairs(state):
        for t in RDK.ItemList(robolink.ITEM_TYPE_TOOL):
            p = t.Parent()
            while p.Valid() and p.item != robot.item:
                p = p.Parent()
            if p.Valid():
                RDK.setCollisionActivePair(state, t, wheel_item)
    for k in range(n):
        q = allsol[:6, k].list()
        if not all(lower[j] <= q[j] <= upper[j] for j in range(6)):
            stats["limit"] += 1; continue
        if wheel:
            r_on = robot.MoveJ_Test(q, q, minstep_deg=1)
            wheel_pairs(robolink.COLLISION_OFF)
            r_off = robot.MoveJ_Test(q, q, minstep_deg=1)
            wheel_pairs(robolink.COLLISION_ON)
            if r_on == 0:
                stats["ok"] += 1; okq = okq or q
            elif r_off == 0:
                stats["wheel"] += 1
            else:
                stats["other"] += 1
        else:
            if robot.MoveJ_Test(q, q, minstep_deg=1) == 0:
                stats["ok"] += 1; okq = okq or q
            else:
                stats["other"] += 1
    return stats, okq

print("=== dissection of (0,-762,300,-90,0,-90) ===")
s_on, _ = dissect((0, -762, 300, -90, 0, -90), wheel=True)
s_off, q_off = dissect((0, -762, 300, -90, 0, -90), wheel=False)
print("  wheel ON : IK=%d limit=%d wheel=%d other=%d OK=%d" % (s_on["ik"], s_on["limit"], s_on["wheel"], s_on["other"], s_on["ok"]))
print("  wheel OFF: IK=%d other=%d OK=%d" % (s_off["ik"], s_off["other"], s_off["ok"]))
if q_off:
    print("  a wheel-OFF-clean sol:", ["%.1f" % v for v in q_off])

# where does the handle axis point in each orientation?
print("\n=== handle (tool Z) axis direction at x=0,y=-762 ===")
for orient in [(180, 0, 180), (-90, 0, -90)]:
    p = f2p(0, -762, 300, *orient)
    R = p.Rot33()
    print("  orient %s -> toolZ world dir = (%.3f, %.3f, %.3f)" % (orient, R[0, 2], R[1, 2], R[2, 2]))
    print("     handle-tip pos (TCP + 24.6mm thickness dir -Z):",
          ["%.1f" % v for v in (p * transl(0, 0, -24.6)).Pos()])

print("\n=== depth scan: (0, y, 300, -90, 0, -90), y=-762..-744, OK-sols (wheel ON) ===")
for y in range(-762, -743, 2):
    s, q = dissect((0, y, 300, -90, 0, -90), wheel=True)
    print("  y=%d : IK=%2d limit=%d wheel=%d other=%d OK=%d" % (y, s["ik"], s["limit"], s["wheel"], s["other"], s["ok"]))

robot.setJoints(HOME)
print("\nrestored:", ["%.2f" % v for v in robot.Joints().list()[:6]])
