# -*- coding: utf-8 -*-
"""恢复+重测：①确保 RUNMODE_RUN_ROBOT；②重试接触位姿 IK；③扫描 rx=180 姿态下
TCP y 从 -740 到 -772 的可达边界，找出实际能到的最深接触位。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Fanuc_2_Pose, invH

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
assert robot.Valid()

# 1) 恢复运行模式
try:
    RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
    print('runmode 已确保 RUN_ROBOT')
except Exception as e:
    print('runmode 恢复异常:', e)

q0 = [float(v) for v in robot.Joints().list()[:6]] if len(robot.Joints().list()) >= 6 else None
print('当前模型关节 =', q0)

def ik_ok(y):
    T = Fanuc_2_Pose([0.0, y, 380.0, 180.0, 0.0, 0.0])
    fl = robot.PoseFrame() * T * invH(robot.PoseTool())
    s = robot.SolveIK_All(fl).tolist()
    if s and isinstance(s[0], (int, float)):
        s = [s]
    return (len(s) > 0), (s[0][:6] if s else None)

# 2) 重测理论接触点
ok, sol = ik_ok(-759.7)
print('重测 (0,-759.7,380,180,0,0) IK =', '有解' if ok else '无解')

# 3) y 边界扫描（-740 → -772）
print('\ny 扫描（rx=180，z=380）：')
last_ok = None
for y10 in range(-7400, -7721, -10):   # 0.1mm 步进太密，改 5mm
    pass
y = -740.0
results = []
while y >= -772.5:
    ok, sol = ik_ok(y)
    results.append((y, ok))
    if ok:
        last_ok = y
    y -= 5.0
for y, ok in results:
    print('  y=%7.1f  %s' % (y, '可达' if ok else '—'))
print('rx=180 下最深可达 y ≈', last_ok)
print('DONE')
