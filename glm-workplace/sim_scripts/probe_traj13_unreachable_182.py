# -*- coding: utf-8 -*-
"""只读：轨迹13 在 tool=182 下的不可达点清单 + 逐点求“TCP z 降到多少可解”。
判据：robot.SolveIK(T, tool=182, reference=frame) 非空；降 z 扫描步长 5mm。
"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT
from robodk.robomath import Fanuc_2_Pose, Pose_2_Fanuc

JSON = r'D:/mydata/working things/dobot_arm/RoboDK files 2/连续轨迹13.json'
BAD = (8, 9, 10, 12, 13)

def solve(robot, vals, tool, frame):
    q = robot.SolveIK(Fanuc_2_Pose(vals), tool=tool, reference=frame)
    try:
        rows = list(q) if not hasattr(q, 'tolist') else q.tolist()
    except Exception:
        rows = []
    # Mat(6,1).tolist() → [6 floats]；空 → []
    flat = []
    for x in rows:
        if isinstance(x, (list, tuple)):
            flat.extend(x)
        else:
            flat.append(x)
    return flat if len(flat) >= 6 else None

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
frame = robot.PoseFrame()
tool182 = Fanuc_2_Pose([0.0, 0.0, 182.0, 0.0, 0.0, 0.0])
tool100 = Fanuc_2_Pose([0.0, 0.0, 100.0, 0.0, 0.0, 0.0])

records = json.load(open(JSON, encoding='utf-8'))
print('总点数:', len(records))
print('%-4s %-8s %-46s %-14s %-14s %s' % ('P', 'type', 'TCP values(x,y,z,rx,ry,rz)', 'tool182', 'tool100', '降z可解'))
for i, rec in enumerate(records, 1):
    vals = [float(v) for v in rec['values']]
    ok182 = solve(robot, vals, tool182, frame)
    ok100 = solve(robot, vals, tool100, frame)
    mark = ''
    if i in BAD or not ok182:
        # 降 z 扫描
        dz_found = None
        for dz in range(0, 405, 5):
            v2 = list(vals)
            v2[2] = vals[2] - dz
            if solve(robot, v2, tool182, frame):
                dz_found = dz
                break
        mark = 'z−%dmm → 可解（新 z=%.1f）' % (dz_found, vals[2] - dz_found) if dz_found is not None else '降400mm仍不可解'
        print('P%-3d %-8s %-46s %-14s %-14s %s' % (
            i, rec.get('type', '-'), ','.join('%.1f' % v for v in vals),
            '可解' if ok182 else '**无解**', '可解' if ok100 else '无解', mark))
print('DONE（只读）')
