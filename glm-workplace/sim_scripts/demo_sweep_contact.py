# -*- coding: utf-8 -*-
"""扫描：面法向压圆柱（0,-1,0）、工具 Z 水平两种朝向（∓X），z=380，
TCP y 从 -700 到 -770，找每种朝向最深可达位。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk import robolink
from robodk.robomath import Mat, invH

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)

def pose_mat(xw, yw, zw, pos):
    m = Mat(4, 4)
    axes = (xw, yw, zw)
    for i in range(3):
        for j in range(3):
            m[i, j] = axes[j][i]
    m[0, 3], m[1, 3], m[2, 3] = pos
    return m

def ik_count(m):
    fl = robot.PoseFrame() * m * invH(robot.PoseTool())
    s = robot.SolveIK_All(fl).tolist()
    if s and isinstance(s[0], (int, float)):
        s = [s]
    return len(s)

# 朝向A: ẑ→(-1,0,0)（法兰在+X侧）  朝向B: ẑ→(+1,0,0)（法兰在-X侧）
orients = {
    'A ẑ→-X': ((0.0, 0.0, -1.0), (0.0, -1.0, 0.0), (-1.0, 0.0, 0.0)),
    'B ẑ→+X': ((0.0, 0.0, 1.0), (0.0, -1.0, 0.0), (1.0, 0.0, 0.0)),
}
for name, (xw, yw, zw) in orients.items():
    print('--- %s ---' % name)
    deepest = None
    for y in range(-700, -771, -5):
        n = ik_count(pose_mat(xw, yw, zw, (0.0, float(y), 380.0)))
        if n:
            deepest = y
            print('  y=%d 有解(%d)' % (y, n))
    print('  最深可达 y =', deepest)
print('DONE')
