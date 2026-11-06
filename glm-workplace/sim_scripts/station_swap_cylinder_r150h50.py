# -*- coding: utf-8 -*-
"""站内几何替换：磨砂圆柱_R180_H40（R180×H40）→ R150×H50。
约定与原 wheel_R180_H40.stl 相同：Z 轴圆柱、原点居中、二进制 STL、180 段（720 三角形）。
流程：生成新 STL → AddFile → 复制父级与位姿 → 碰撞配对可用性验证 → 删旧 → 改回原名。
不保存工作站。"""
import sys, io, struct, math, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import Robolink, ITEM_TYPE_OBJECT

OLD_NAME = '磨砂圆柱_R180_H40'
STL_OUT = r'D:\mydata\glm-workplace\tools\cylinder_R150_H50.stl'
R, H, N = 150.0, 50.0, 180

def write_cylinder_stl(path, r, h, n):
    """Z 轴、z∈[-h/2,h/2]、原点居中的二进制圆柱 STL。"""
    tris = []
    zt, zb = h / 2.0, -h / 2.0
    ring = [(r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n)) for k in range(n)]
    for k in range(n):
        x1, y1 = ring[k]
        x2, y2 = ring[(k + 1) % n]
        # 侧面两三角（外法线）
        nx, ny = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        ln = math.hypot(nx, ny)
        nrm = (nx / ln, ny / ln, 0.0)
        tris.append((nrm, (x1, y1, zb), (x2, y2, zb), (x2, y2, zt)))
        tris.append((nrm, (x1, y1, zb), (x2, y2, zt), (x1, y1, zt)))
    # 顶/底扇
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
old = RDK.Item(OLD_NAME)
assert old.Valid(), '未找到 ' + OLD_NAME
pose = old.Pose()
parent = old.Parent()
assert parent.Valid(), '旧圆柱无父级'
print('旧对象：parent=%s pose=%s' % (parent.Name(), ['%.3f' % v for v in pose.Pos()]))

new_item = RDK.AddFile(STL_OUT)
print('AddFile ->', new_item.Name(), 'valid=', new_item.Valid())
new_item.setParent(parent)
new_item.setPose(pose)
new_item.setVisible(True)

# 配对验证：宏的 _enable_obstacle_checks 用 setCollisionActivePair(robot, obstacle)
from robodk.robolink import ITEM_TYPE_ROBOT
robot = RDK.Item('', ITEM_TYPE_ROBOT)
assert robot.Valid(), '未找到机器人'
ok = RDK.setCollisionActivePair(1, robot, new_item, 0, 0)
print('碰撞配对 setCollisionActivePair(robot, new) =', ok)

old.Delete()
new_item.setName(OLD_NAME)
final = RDK.Item(OLD_NAME)
print('回读：name=%s valid=%s' % (final.Name(), final.Valid()))
pf = final.Pose()
print('回读：pose pos=%s（与旧位姿一致=%s）' % (
    ['%.3f' % v for v in pf.Pos()],
    max(abs(a - b) for a, b in zip(list(pf.Pos()), list(pose.Pos()))) < 1e-6))
print('父级=%s' % final.Parent().Name())
print('DONE：站内磨砂圆柱已改为 R150×H50（名称保留原字符串以兼容预检；不保存工作站）')
