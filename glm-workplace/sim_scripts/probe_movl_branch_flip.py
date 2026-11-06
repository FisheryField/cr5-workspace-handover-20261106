# -*- coding: ascii -*-
# Hypothesis: driver MOVL re-solved IK into a flipped branch and joint-interpolated.
# Test: is STOP on the joint-interp path P4 -> B for some IK branch B of the P5 pose?
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT
from robodk.robomath import invH
import math

RDK = Robolink()
r = RDK.Item('', ITEM_TYPE_ROBOT)
frame, tool = r.PoseFrame(), r.PoseTool()

P4 = [-73.27186167655573, -18.940837834556703, -93.25753304820469,
      -67.80162911723862, -73.2718616765557, -180.0]
P5 = [-63.41392174214575, -23.452600702069375, -86.6540412190377,
      -69.8933580788929, -63.41392174214576, -180.0]
STOP = [-69.33154278464865, -45.82446435349989, -48.85376368586522,
        -85.10061064072327, -69.6629164475899, -180.17595039849937]

target = (invH(frame) * r.SolveFK(P5) * tool)          # P5 pose (active tool)
flange = frame * target * invH(tool)
rows = r.SolveIK_All(flange).tr().rows
print('IK branches of P5 pose: %d' % len(rows))
best = None
for B in rows:
    B = [((float(v) + 180.0) % 360.0) - 180.0 for v in B[:6]]
    # least-squares progress t of STOP along P4->B (per-axis scale-free)
    num = sum((s - a) * (b - a) for a, s, b in zip(P4, STOP, B) if a != b)
    den = sum((b - a) ** 2 for a, b in zip(P4, B) if a != b)
    t = num / den if den else 0.0
    err = max(abs((a + (b - a) * t) - s) for a, s, b in zip(P4, STOP, B))
    if best is None or err < best[0]:
        best = (err, t, B[:])
print('best branch fit: max per-axis mismatch = %.2f deg at progress t=%.2f' % (best[0], best[1]))
print('branch joints:', [round(v, 2) for v in best[2]])
if best[0] < 3.0:
    print('=> MATCH: driver MOVL was joint-interpolating toward a DIFFERENT IK branch of P5.')
else:
    print('=> no branch matches; divergence is not a plain branch flip.')
# how close is that branch path to the cylinder at its worst?
AX = (0.0, -956.0)
worst = 1e9
for i in range(21):
    tt = i / 20.0
    q = [a + (b - a) * tt for a, b in zip(P4, best[2])]
    p = (invH(frame) * r.SolveFK(q) * tool).Pos()
    worst = min(worst, math.hypot(p[0] - AX[0], p[1] - AX[1]))
print('joint path P4->that branch: min radial distance to cyl axis = %.1f mm (R=180)' % worst)
