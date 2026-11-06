# -*- coding: utf-8 -*-
"""把手网格手术 v3（2026-10-20，配合 v14w27 工具=182）：
- 用户定案：把手不动、杆伸到 182 ⇒ 现有网格（handle_shortened_99，z∈[0,99]）全量保留，
  补一根连续矩形杆覆盖 z∈[5,182]（含两处历史手术断口 z[4.5,34.5]/[74.5,84.5]），
  杆截面取现有杆段最大包络 X±3.75 × Z±10.8（局部系）。
- 局部系约定：local Y = 工具轴反向，world z = 159.5 − localY（法兰 z=0，tip z 大）。
  ⇒ z=182 ⇔ localY=−22.5；z=5 ⇔ localY=154.5（杆上端取 156 与安装块微搭接，消灭 0.5mm 缝）。
- 站内替换：删旧 → AddFile → parent=机器人、pose=identity、GeometryPose 原值、名 门把手_bs1。
- 重建自碰对 links1-6↔把手；障碍物对由宏按名循环负责。
- 不保存工作站。
"""
import sys, io, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT
from robodk.robomath import Fanuc_2_Pose, Pose_2_Fanuc, eye

SRC = r'D:\mydata\glm-workplace\tools\handle_shortened_99.stl'
OUT = r'D:\mydata\glm-workplace\tools\handle_rod_182.stl'
NAME = '门把手_bs1'

# ---- 杆盒（局部系）----
Y_MIN, Y_MAX = -22.5, 156.0     # z: 182 → 3.5
X_MIN, X_MAX = -3.75, 3.75
Z_MIN, Z_MAX = -10.8, 10.8

CORNERS = [
    (X_MIN, Y_MIN, Z_MIN), (X_MAX, Y_MIN, Z_MIN), (X_MAX, Y_MAX, Z_MIN), (X_MIN, Y_MAX, Z_MIN),
    (X_MIN, Y_MIN, Z_MAX), (X_MAX, Y_MIN, Z_MAX), (X_MAX, Y_MAX, Z_MAX), (X_MIN, Y_MAX, Z_MAX),
]
# 12 三角（绕序按右手，外向）
FACES = [
    (0, 2, 1), (0, 3, 2),   # z- 底
    (4, 5, 6), (4, 6, 7),   # z+ 顶
    (0, 1, 5), (0, 5, 4),   # y- (远端)
    (2, 3, 7), (2, 7, 6),   # y+ (法兰端)
    (1, 2, 6), (1, 6, 5),   # x+
    (3, 0, 4), (3, 4, 7),   # x-
]

def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])

def norm(v):
    import math
    l = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2) or 1.0
    return (v[0] / l, v[1] / l, v[2] / l)

# ---- 读原网格 ----
d = open(SRC, 'rb').read()
n0 = struct.unpack_from('<I', d, 80)[0]
tris = []
off = 84
for i in range(n0):
    base = off + i * 50
    v = struct.unpack_from('<12f', d, base)  # normal + 3 verts
    tris.append(v)

# ---- 追加杆盒 ----
added = 0
for f in FACES:
    p = [CORNERS[j] for j in f]
    nrm = norm(cross(sub(p[1], p[0]), sub(p[2], p[0])))
    tris.append((nrm[0], nrm[1], nrm[2],
                 p[0][0], p[0][1], p[0][2],
                 p[1][0], p[1][1], p[1][2],
                 p[2][0], p[2][1], p[2][2]))
    added += 1

# ---- 写二进制 STL ----
buf = bytearray(80 + 4 + 50 * len(tris))
_hdr = (b'handle_rod_182 v14w27 tool=182 rod-fill+extend')
buf[0:80] = (_hdr + b' ' * 80)[:80]
struct.pack_into('<I', buf, 80, len(tris))
for i, t in enumerate(tris):
    struct.pack_into('<12f', buf, 84 + i * 50, *t)
    struct.pack_into('<H', buf, 84 + i * 50 + 48, 0)
open(OUT, 'wb').write(bytes(buf))

# 包围盒复核
xs = [t[j] for t in tris for j in (3, 6, 9)]
ys = [t[j] for t in tris for j in (4, 7, 10)]
zs = [t[j] for t in tris for j in (5, 8, 11)]
print('STL 写出: %s  三角 %d（原 %d + 杆 %d）' % (OUT, len(tris), n0, added))
print('  局部 bbox X[%.2f,%.2f] Y[%.2f,%.2f] Z[%.2f,%.2f]' % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
print('  → 工具轴 world z = 159.5 − Y ⇒ 覆盖 z[%.1f, %.1f]（目标 [−5.5, 182]）'
      % (159.5 - max(ys), 159.5 - min(ys)))

# ---- 站内替换 ----
RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
assert robot.Valid()
old = RDK.Item(NAME)
assert old.Valid(), '未找到 ' + NAME
old.Delete()
item = RDK.AddFile(OUT)
item.setParent(robot)
p = item.Pose()
if any(abs(v) > 1e-9 for v in p.Pos()) or Pose_2_Fanuc(p)[3] != 0:
    item.setPose(eye(4))
item.setName(NAME)
item.setGeometryPose(Fanuc_2_Pose([0.0, 0.0, 159.5, -90.0, 0.0, 0.0]))
item.setVisible(True)
print('站内替换: name=%s parent=%s' % (item.Name(), item.Parent().Name()))
print('  geo =', ['%.3f' % v for v in Pose_2_Fanuc(item.GeometryPose())])

# ---- 自碰对（links1-6 ↔ 把手）----
ok_all = True
for link in range(1, 7):
    ok = RDK.setCollisionActivePair(1, robot, item, link, 0)
    ok_all = ok_all and (ok == 1)
print('自碰对 links1-6 全部建立 =', ok_all)
print('DONE（未保存工作站）')
