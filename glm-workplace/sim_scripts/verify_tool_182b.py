# -*- coding: utf-8 -*-
"""只读：弄清 robomath.Mat 的取值/判空姿势，并正确验证 tool=182 的 IK 语义。"""
from robodk.robolink import *
from robodk.robomath import *

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
if not robot.Valid():
    raise SystemExit('ERROR: 未找到机器人')

frame = robot.PoseFrame()
T = Fanuc_2_Pose([500.0, 0.0, 300.0, 180.0, 0.0, 0.0])
q = robot.SolveIK(T, tool=robot.PoseTool(), reference=frame)

print('type:', type(q))
print('len(q):', len(q))
try:
    print('len(q.rows()):', len(q.rows()))
except Exception as e:
    print('q.rows() EXC:', e)
tl = q.tolist()
print('tolist type/len:', type(tl), len(tl))
print('tolist:', tl)


def mat_vals(m):
    """取 (6,1)/(1,6)/empty Mat 的 6 个关节值；不足返回 None。"""
    try:
        rows = m.rows()
    except Exception:
        rows = []
    vals = []
    for r in rows:
        if isinstance(r, (list, tuple)):
            vals.extend(float(v) for v in r)
        else:
            vals.append(float(r))
    if len(vals) < 6:
        # 容错：单行列结构
        t = m.tolist()
        flat = []
        for x in t:
            if isinstance(x, (list, tuple)):
                flat.extend(float(v) for v in x)
            else:
                flat.append(float(x))
        vals = flat
    return vals[:6] if len(vals) >= 6 else None


qv = mat_vals(q)
print('qv:', qv)

if qv:
    framep = robot.PoseFrame()
    tcp = invH(framep) * robot.SolveFK(q) * robot.PoseTool()
    flg = invH(framep) * robot.SolveFK(q)
    print('d(TCP,T)   = %.3f mm  (≈0)' % norm((invH(T) * tcp).Pos()))
    print('d(Flange,T)= %.3f mm  (≈182)' % norm((invH(T) * flg).Pos()))

    T2 = Fanuc_2_Pose([0.0, -775.0, 300.0, 90.0, 0.0, 0.0])
    q2 = robot.SolveIK(T2, tool=robot.PoseTool(), reference=framep)
    qv2 = mat_vals(q2)
    print('pose2 qv:', qv2)
    if qv2:
        tcp2 = invH(framep) * robot.SolveFK(q2) * robot.PoseTool()
        print('pose2 d(TCP,T2) = %.3f mm' % norm((invH(T2) * tcp2).Pos()))

    # 对照：不带 tool —— pose 按法兰解
    q3 = robot.SolveIK(T)
    qv3 = mat_vals(q3)
    print('对照(不带tool) qv:', qv3)
    if qv3:
        flg3 = robot.SolveFK(q3)
        print('对照 d(Flange,T) = %.3f mm (≈0 => pose 即法兰)' % norm((invH(T) * flg3).Pos()))
        tcp3 = flg3 * robot.PoseTool()
        print('对照 d(TCP,T)    = %.3f mm (≈182)' % norm((invH(T) * tcp3).Pos()))
else:
    print('!!! tool=182 下该位姿确实无解')

print('DONE（只读）')
