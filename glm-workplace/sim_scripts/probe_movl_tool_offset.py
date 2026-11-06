# -*- coding: ascii -*-
# Hypothesis 2: driver MOVL ignores the active tool offset.
# If so, the FLANGE at STOP should sit at the COMMANDED P5 TCP pose
# (commanded TCP = P5 pose; real TCP = flange + 159.63mm tool along flange z).
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT
from robodk.robomath import invH
import math

RDK = Robolink()
r = RDK.Item('', ITEM_TYPE_ROBOT)
frame, tool = r.PoseFrame(), r.PoseTool()

P5 = [-63.41392174214575, -23.452600702069375, -86.6540412190377,
      -69.8933580788929, -63.41392174214576, -180.0]
STOP = [-69.33154278464865, -45.82446435349989, -48.85376368586522,
        -85.10061064072327, -69.6629164475899, -180.17595039849937]

cmd_tcp = invH(frame) * r.SolveFK(P5) * tool     # commanded P5 TCP pose (frame coords)
stop_fk = invH(frame) * r.SolveFK(STOP)           # STOP flange pose (frame coords)

pc, pf = cmd_tcp.Pos(), stop_fk.Pos()
print('commanded P5 TCP pos : %s' % [round(v, 2) for v in pc])
print('STOP flange pos      : %s' % [round(v, 2) for v in pf])
print('delta                : %s  |d|=%.1f mm' % ([round(b - a, 2) for a, b in zip(pc, pf)],
      math.sqrt(sum((b - a) ** 2 for a, b in zip(pc, pf)))))

# also compare STOP TCP vs commanded (for scale)
stop_tcp = stop_fk * tool
pt = stop_tcp.Pos()
print('STOP real TCP pos    : %s  (delta to cmd: %.1f mm)' % (
    [round(v, 2) for v in pt], math.sqrt(sum((b - a) ** 2 for a, b in zip(pc, pt)))))

# angle between the STOP->cmd offset vector and the flange z axis at STOP
R = stop_fk
zx, zy, zz = R[0, 2], R[1, 2], R[2, 2]
d = [b - a for a, b in zip(pf, pc)]
n = math.sqrt(sum(v * v for v in d))
cosang = (d[0] * zx + d[1] * zy + d[2] * zz) / n if n else 0
print('flange z axis at STOP: [%0.3f %0.3f %0.3f]; offset vector angle to it: %.1f deg' % (zx, zy, zz, math.degrees(math.acos(max(-1, min(1, cosang))))))
