# -*- coding: utf-8 -*-
"""站内几何替换：磨砂圆柱 半径 150 → 140（H50 不变，x/z 位姿不变）。
约定同 station_swap_cylinder_r150h50.py：Z 轴圆柱、原点居中、二进制 STL、180 段。
名称保留原字符串 '磨砂圆柱_R150_H50' 以兼容宏预检（用户要求代码后面集中修改）。
不保存工作站。"""
import sys, io, struct, math, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import Robolink, ITEM_TYPE_OBJECT, ITEM_TYPE_ROBOT

CUR_NAME = '磨砂圆柱_R150_H50'   # 名称暂留（含 R150 字样，后续随代码集中修正）
STL_OUT = r'D:\mydata\glm-workplace\tools\cylinder_R140_H50.stl'
R, H, N = 140.0, 50.0, 180

def write_cylinder_stl(path, r, h, n):
    tris = []
    zt, zb = h / 2.0, -h / 2.0
    ring = [(r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n)) for k in range(n)]
    for k in range(n):
        x1, y1 = ring[k]
        x2, y2 = ring[(k + 1) % n]
        nx, ny = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        ln = math.hypot(nx, ny)
        nrm = (nx / ln, ny / ln, 0.0)
        tris.append((nrm, (x1, y1, zb), (x2, y2, zb), (x2, y2, zt)))
        tris.append((nrm, (x1, y1, zb), (x2, y2, zt), (x1, y1, zt)))
    for k in range(n):
        x1, y1 = ring[k]
        x2, y2 = ring[(k + 1) % n]
        tris.append(((0.0, 0.0, 1.0), (0.0, 0.0, zt), (x1, y1, zt), (x2, y2, zt)))
        tris.append(((0.0, 0.0, -1.0), (0.0, 0.0, zb), (x2, y2, zb), (x1, y1, zb)))
    buf = bytearray(b'\x00' * 80 + struct.pack('<I', len(tris)))
    for nrm, a, b, c in tris:
        buf += struct.pack('<12fH', *nrm, *a, *b, *c, 0)
    with open(path, 'wb') as f:
        f.write(buf)
    return len(tris)

ntri = write_cylinder_stl(STL_OUT, R, H, N)
print('已生成 %s（%d 三角形，R%.0f×H%.0f）' % (STL_OUT, ntri, R, H))

RDK = Robolink()
cur = RDK.Item(CUR_NAME)
assert cur.Valid(), '未找到 ' + CUR_NAME
pose = cur.Pose()
parent = cur.Parent()
assert parent.Valid(), '圆柱无父级'
print('旧对象：parent=%s pose_pos=(%.3f, %.3f, %.3f)' % (
    parent.Name(), pose[0, 3], pose[1, 3], pose[2, 3]))

new_item = RDK.AddFile(STL_OUT)
print('AddFile ->', new_item.Name(), 'valid=', new_item.Valid())
new_item.setParent(parent)
new_item.setPose(pose)
new_item.setVisible(True)

robot = RDK.Item('', ITEM_TYPE_ROBOT)
assert robot.Valid(), '未找到机器人'
ok = RDK.setCollisionActivePair(1, robot, new_item, 0, 0)
print('碰撞配对 setCollisionActivePair(robot, new) =', ok)

cur.Delete()
new_item.setName(CUR_NAME)
final = RDK.Item(CUR_NAME)
pf = final.Pose()
print('回读：name=%s valid=%s' % (final.Name(), final.Valid()))
print('回读：pose_pos=(%.3f, %.3f, %.3f)（x/z 与旧一致=%s）' % (
    pf[0, 3], pf[1, 3], pf[2, 3],
    abs(pf[0, 3] - pose[0, 3]) < 1e-9 and abs(pf[2, 3] - pose[2, 3]) < 1e-9))
print('父级=%s' % final.Parent().Name())
print('DONE：站内圆柱已改为 R140×H50（名称暂留原字符串；未保存工作站）')
