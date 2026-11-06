# -*- coding: utf-8 -*-
"""只读：工作点 W=(0,-781,470)（圆柱面前 1mm）上的可达朝向普查（tool=182）。
rx ∈ {-90,0,90,180}，rz ∈ {-180,-90,0,90,180}，并附 (100,-781) 与 (35,-781) 抽查。
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT
from robodk.robomath import Fanuc_2_Pose

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
frame = robot.PoseFrame()
tool = Fanuc_2_Pose([0.0, 0.0, 182.0, 0.0, 0.0, 0.0])

def ok(x, y, z, rx, ry, rz):
    q = robot.SolveIK(Fanuc_2_Pose([float(x), float(y), float(z), float(rx), float(ry), float(rz)]),
                      tool=tool, reference=frame)
    try:
        t = q.tolist()
    except Exception:
        t = []
    flat = []
    for v in t:
        flat.extend(v if isinstance(v, (list, tuple)) else [v])
    return len(flat) >= 6

print('=== 工作点 (0, -781, 470) ===')
for rx in (-90.0, 0.0, 90.0, 180.0):
    row = []
    for rz in (-180.0, -90.0, 0.0, 90.0, 180.0):
        r = '✓' if ok(0, -781, 470, rx, 0, rz) else '✗'
        row.append('%s:%s' % (int(rz), r))
    print('rx=%-5s  %s' % (int(rx), '  '.join(row)))

print('=== 抽查 (100,-781,470) rx=±90 ===')
for rx in (-90.0, 90.0):
    for rz in (0.0, 180.0, 90.0):
        print('x=100 rx=%-4d rz=%-4d -> %s' % (int(rx), int(rz), '✓' if ok(100, -781, 470, rx, 0, rz) else '✗'))
print('=== 抽查 (35,-781,470) rx90 rz90（自转位姿） ===')
print('->', '✓' if ok(35, -781, 470, 90, 0, 90) else '✗')
print('=== 工作点面表 (0,-782,470) 接触位（仅记录，不建议） ===')
for rx in (-90.0, 90.0):
    print('rx=%-4d -> %s' % (int(rx), '✓' if ok(0, -782, 470, rx, 0, 0) else '✗'))
print('DONE')
