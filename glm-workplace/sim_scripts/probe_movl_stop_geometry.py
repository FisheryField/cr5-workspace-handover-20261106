# -*- coding: ascii -*-
# Probe: where did the failed MOVL stop relative to the certified P4->P5 line?
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT
from robodk.robomath import invH
import math

RDK = Robolink()
r = RDK.Item('', ITEM_TYPE_ROBOT)
frame = r.PoseFrame()
tool = r.PoseTool()

def tcp_of(q):
    return (invH(frame) * r.SolveFK(list(q)) * tool).Pos()

P4 = [-73.27186167655573, -18.940837834556703, -93.25753304820469,
      -67.80162911723862, -73.2718616765557, -180.0]
P5 = [-63.41392174214575, -23.452600702069375, -86.6540412190377,
      -69.8933580788929, -63.41392174214576, -180.0]
STOP = [-69.33, -45.82, -48.85, -85.10, -69.66, -180.18]
AX = (0.0, -956.0)   # cylinder axis (pose Pos)

def rad(p):
    return math.hypot(p[0] - AX[0], p[1] - AX[1])

p4, p5, ps = tcp_of(P4), tcp_of(P5), tcp_of(STOP)
print('P4   tcp %s  r_axis=%.1f' % ([round(v, 1) for v in p4], rad(p4)))
print('P5   tcp %s  r_axis=%.1f' % ([round(v, 1) for v in p5], rad(p5)))
print('STOP tcp %s  r_axis=%.1f' % ([round(v, 1) for v in ps], rad(ps)))

ax, ay = p4[0], p4[1]
bx, by = p5[0], p5[1]
px, py = ps[0], ps[1]
dx, dy = bx - ax, by - ay
L2 = dx * dx + dy * dy
t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
dline = math.hypot(px - (ax + t * dx), py - (ay + t * dy))
dz = ps[2] - (p4[2] + t * (p5[2] - p4[2]))
print('STOP distance to certified LINE: lateral=%.1f mm  dz=%.1f mm  (proj t=%.2f)' % (dline, dz, t))

best = min((math.hypot(ax + i / 20.0 * dx - AX[0], ay + i / 20.0 * dy - AX[1]), i / 20.0) for i in range(21))
print('certified LINE min radial distance to cyl axis: %.1f mm at t=%.2f' % best)

print('--- joint-interpolation P4->P5 radial profile (what a MOVJ-like path does) ---')
for i in range(11):
    tt = i / 10.0
    q = [a + (b - a) * tt for a, b in zip(P4, P5)]
    p = tcp_of(q)
    print('  t=%.1f  tcp %s  r_axis=%7.1f  z=%.1f' % (tt, [round(v, 1) for v in p], rad(p), p[2]))

print('--- joint-space progress of STOP along P4->P5 (per axis) ---')
for j in range(5):
    span = P5[j] - P4[j]
    print('  J%d: fraction=%.2f' % (j + 1, (STOP[j] - P4[j]) / span if abs(span) > 1e-9 else float('nan')))
