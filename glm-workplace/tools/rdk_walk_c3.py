#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# C plan: pose family with flange Z axis along +/-Y, TCP at wheel center height,
# find the pose whose -Z face touches the wheel rim, then move, report, snapshot, go home.
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from robodk import robolink, robomath

RDK = robolink.Robolink()
robot = RDK.Item("Dobot CR5", robolink.ITEM_TYPE_ROBOT)
state_raw = robot.ConnectedState()
state = state_raw[0] if isinstance(state_raw, tuple) else state_raw
if state not in (robolink.ROBOTCOM_DISCONNECTED, robolink.ROBOTCOM_NOT_CONNECTED, -1, 0, None):
    print("ABORT: robot driver connected"); sys.exit(2)
RDK.setRunMode(robolink.RUNMODE_SIMULATE)

def report(tag):
    T = robot.Pose()
    zcol = [T[0, 2], T[1, 2], T[2, 2]]
    tcp = [T[0, 3], T[1, 3], T[2, 3]]
    fn = [tcp[k] - 12.3 * zcol[k] for k in range(3)]
    fp = [tcp[k] + 12.3 * zcol[k] for k in range(3)]
    print("[%s] TCP=(%.1f,%.1f,%.1f) -Zface=(%.1f,%.1f,%.1f) gap=%+.2f | +Zface gap=%+.2f" % (
        tag, tcp[0], tcp[1], tcp[2], fn[0], fn[1], fn[2], fn[1] - (-776), fp[1] - (-776)))

print("== +/-Y side candidates ==")
best = None
for rx in (-90, 90):
    for rz in (-180, 0, 180):
        for tcp_y in (-943.7, -968.3):
            vals = [0, tcp_y, 300, rx, 0, rz]
            pose = robomath.xyzrpw_2_pose(vals)
            try:
                ik = robot.SolveIK(pose)
                ikl = ik.list() if hasattr(ik, "list") else list(ik)
                ok = len(ikl) == 6 and all(q == q for q in ikl)
            except Exception:
                ok = False
            if not ok:
                print("  unreachable (%3d,0,%4d) y=%7.1f" % (rx, rz, tcp_y))
                continue
            T = pose
            fz_dir = -T[1, 2]
            print("  reach (%3d,0,%4d) y=%7.1f  -Zface-y-dir=%+.2f  j=%s" % (rx, rz, tcp_y, fz_dir, [round(x,1) for x in ikl]))
            if fz_dir < -0.9:
                best = vals

if best:
    print()
    print("== moving to:", best)
    robot.MoveJ(robomath.xyzrpw_2_pose(best), blocking=True)
    report("C-final %s" % best[3:])
    print("  joints:", [round(x, 3) for x in robot.Joints().list()])
    RDK.Command("SnapShot", r"D:\mydata\glm-workplace\data\screens\rdk_view_C.png")
    print("SnapShot C exported")
else:
    print("!! no feasible -Z-face-on-wheel solution")

j0 = json.load(open(r"D:\mydata\glm-workplace\data\scripts_ref\sim_walk_j0.json", encoding="utf-8"))
robot.MoveJ(j0, blocking=True)
print("back home, joints:", [round(x, 3) for x in robot.Joints().list()])
print("done")
