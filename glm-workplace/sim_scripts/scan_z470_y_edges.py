# -*- coding: utf-8 -*-
"""只读扫描：tool=182、z=470 固定下，各姿态族的最远可达 y 边界（x 分别 0/35/40/100）。
判据：robot.SolveIK(T, tool=182, reference=frame) 非空（tolist 长度≥6）。
输出每族 edge_y（最负可解）与建议工作 y（edge+20，5 取整）。
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT
from robodk.robomath import Fanuc_2_Pose

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
frame = robot.PoseFrame()
tool = Fanuc_2_Pose([0.0, 0.0, 182.0, 0.0, 0.0, 0.0])

def solvable(x, y, z, rx, ry, rz):
    q = robot.SolveIK(Fanuc_2_Pose([float(x), float(y), float(z), float(rx), float(ry), float(rz)]),
                      tool=tool, reference=frame)
    try:
        t = q.tolist()
    except Exception:
        t = []
    flat = []
    for v in t:
        if isinstance(v, (list, tuple)):
            flat.extend(v)
        else:
            flat.append(v)
    return len(flat) >= 6

Z = 470.0
FAMILIES = [
    ('rx180 rz0   (P8族 x0)',   [(0.0, 180.0, 0.0, 0.0)]),
    ('rx180 rz180 (P11/12族 x0)',[(0.0, 180.0, 0.0, 180.0)]),
    ('rx180 rz0   (P10族 x100)',[(100.0, 180.0, 0.0, 0.0)]),
    ('rx180 rz180 (P11族 x100)',[(100.0, 180.0, 0.0, 180.0)]),
    ('rx-90 rz180 (P2/3族 x0)', [(0.0, -90.0, 0.0, 180.0)]),
    ('rx-90 rz180 (P3族 x100)', [(100.0, -90.0, 0.0, 180.0)]),
    ('rx90  rz0   (P4/5族)',    [(0.0, 90.0, 0.0, 0.0), (100.0, 90.0, 0.0, 0.0)]),
    ('rx90  rz90  (P13-15族)',  [(0.0, 90.0, 0.0, 90.0), (40.0, 90.0, 0.0, 90.0)]),
    ('rx90  rz90  (P16-19族 x35/40)', [(35.0, 90.0, 0.0, 90.0), (40.0, 90.0, 0.0, 90.0)]),
    ('rx180 (P6/7族 x0 二次确认)', [(0.0, 180.0, 0.0, 0.0)]),
]

for name, variants in FAMILIES:
    for (x, rx, ry, rz) in variants:
        edge = None
        y = -500.0
        last_ok = None
        while y >= -860.0:
            if solvable(x, y, Z, rx, ry, rz):
                last_ok = y
                y -= 5.0
            else:
                break
        if last_ok is not None:
            sug = (last_ok + 20.0) // 5 * 5
            print('%-28s x=%-5.0f  edge_y=%7.1f   建议 y=%7.1f' % (name, x, last_ok, sug))
        else:
            print('%-28s x=%-5.0f  y=-500 已无解' % (name, x))

# 额外：P7 位置复核（y=-560, rx180）与 P1/P21
for (x, y, rx, rz) in [(500, 0, 180, 0), (-600, 0, 180, -90), (0, -560, 180, 0)]:
    print('复核 (%.0f,%.0f,470,%.0f,0,%.0f) -> %s' % (x, y, rx, rz, '可解' if solvable(x, y, Z, rx, 0, rz) else '无解'))
print('DONE（只读）')
