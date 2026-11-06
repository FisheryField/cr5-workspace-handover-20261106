# -*- coding: utf-8 -*-
"""把手网格手术 v4（2026-10-20，纠正版，配合 v14w27 工具=182）：
用户定案（澄清后）：最末端是把手本身——连接件（法兰面→把手）加长，
把手组件整体外移，【把手工作点 = 法兰前 182mm】。

做法：
- 基底 handle_shortened_99.stl（连通组件分析：仅 2 组件，撕裂面 z=39.4 / 局部 Y=120.13）
  · comp1 把手侧（含侧向抓手 X→107.78）：整体局部 Y −83（→ world z +83），尖端 99→182
  · comp2 法兰侧连接件：原位不动
- 追加连续矩形杆（X±3.75 × Z±10.8，局部 Y∈[−22.5,156] ⇒ z∈[3.5,182]）：
  覆盖加长后的连接段（z39.4→122.4）并贯穿全程（union，不伤害既有几何）。
  注：基底网格本无断口（剖面“空带”是长三角形杆，无中间顶点），杆盒作用=延长段+微搭接。
- 站内替换：删旧 → AddFile → parent=机器人、pose=identity、GeometryPose 原值、名 门把手_bs1
- 重建自碰对 links1-6；不保存工作站。
输出：tools\\handle_rod_182_v2.stl
"""
import sys, io, struct, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from collections import defaultdict
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT
from robodk.robomath import Fanuc_2_Pose, Pose_2_Fanuc, eye

SRC = r'D:\mydata\glm-workplace\tools\handle_shortened_99.stl'
OUT = r'D:\mydata\glm-workplace\tools\handle_rod_182_v2.stl'
NAME = '门把手_bs1'
SHIFT_Y = -83.0            # 把手组件外移：local Y −83 ⇔ world z +83

# ---- 读取三角与顶点（量化合并共享顶点）----
d = open(SRC, 'rb').read()
n = struct.unpack_from('<I', d, 80)[0]
verts, vmap, tris = [], {}, []

def vid(x, y, z):
    k = (round(x, 4), round(y, 4), round(z, 4))
    i = vmap.get(k)
    if i is None:
        i = len(verts); vmap[k] = i; verts.append(k)
    return i

off = 84
for i in range(n):
    v = struct.unpack_from('<9f', d, off + i * 50 + 12)
    tris.append((vid(v[0], v[1], v[2]), vid(v[3], v[4], v[5]), vid(v[6], v[7], v[8])))

# ---- 连通组件（union-find）----
par = list(range(len(verts)))
def find(a):
    while par[a] != a:
        par[a] = par[par[a]]; a = par[a]
    return a
def uni(a, b):
    ra, rb = find(a), find(b)
    if ra != rb: par[rb] = ra
for a, b, c in tris:
    uni(a, b); uni(b, c)

# ---- 找把手组件：包含 X>50 顶点（侧向抓手）的组件 ----
handle_root = None
for i, (x, y, z) in enumerate(verts):
    if x > 50:
        handle_root = find(i); break
assert handle_root is not None, '未找到侧向抓手顶点'

moved = 0
new_verts = []
for i, (x, y, z) in enumerate(verts):
    if find(i) == handle_root:
        new_verts.append((x, y + SHIFT_Y, z)); moved += 1
    else:
        new_verts.append((x, y, z))

ys_moved = [new_verts[i][1] for i in range(len(verts)) if find(i) == handle_root]
print('把手组件顶点 %d 个，Y %0.2f..%0.2f → %0.2f..%0.2f（world z %0.1f..%0.1f）'
      % (moved, min(v[1] for i, v in enumerate(verts) if find(i) == handle_root),
         max(v[1] for i, v in enumerate(verts) if find(i) == handle_root),
         min(ys_moved), max(ys_moved), 159.5 - max(ys_moved), 159.5 - min(ys_moved)))

# ---- 追加延长杆盒（局部系 Y∈[−22.5,156] ⇒ z∈[3.5,182]）----
Y_MIN, Y_MAX = -22.5, 156.0
X_MIN, X_MAX = -3.75, 3.75
Z_MIN, Z_MAX = -10.8, 10.8
CORNERS = [
    (X_MIN, Y_MIN, Z_MIN), (X_MAX, Y_MIN, Z_MIN), (X_MAX, Y_MAX, Z_MIN), (X_MIN, Y_MAX, Z_MIN),
    (X_MIN, Y_MIN, Z_MAX), (X_MAX, Y_MIN, Z_MAX), (X_MAX, Y_MAX, Z_MAX), (X_MIN, Y_MAX, Z_MAX),
]
FACES = [(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(2,3,7),(2,7,6),(1,2,6),(1,6,5),(3,0,4),(3,4,7)]

def sub(a, b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def unit(v):
    l = math.sqrt(v[0]**2+v[1]**2+v[2]**2) or 1.0
    return (v[0]/l, v[1]/l, v[2]/l)

tris_out = []   # (normal, v1, v2, v3) 各 (x,y,z)
for a, b, c in tris:
    p1, p2, p3 = new_verts[a], new_verts[b], new_verts[c]
    nrm = unit(cross(sub(p2, p1), sub(p3, p1)))
    tris_out.append((nrm, p1, p2, p3))
for f in FACES:
    p = [CORNERS[j] for j in f]
    nrm = unit(cross(sub(p[1], p[0]), sub(p[2], p[0])))
    tris_out.append((nrm, p[0], p[1], p[2]))

# ---- 写二进制 STL ----
buf = bytearray(84 + 50 * len(tris_out))
_hdr = b'handle_rod_182_v2 handle-at-end wp=182 v14w27'
buf[0:80] = (_hdr + b' ' * 80)[:80]
struct.pack_into('<I', buf, 80, len(tris_out))
for i, (nrm, p1, p2, p3) in enumerate(tris_out):
    struct.pack_into('<12fH', buf, 84 + i * 50,
                     nrm[0], nrm[1], nrm[2],
                     p1[0], p1[1], p1[2], p2[0], p2[1], p2[2], p3[0], p3[1], p3[2], 0)
open(OUT, 'wb').write(bytes(buf))

xs = [p[0] for t in tris_out for p in t[1:]]
ys = [p[1] for t in tris_out for p in t[1:]]
zs = [p[2] for t in tris_out for p in t[1:]]
print('STL: %s  三角=%d（基底 %d + 杆 12）' % (OUT, len(tris_out), n))
print('  局部 bbox X[%.2f,%.2f] Y[%.2f,%.2f] Z[%.2f,%.2f]' % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
print('  → world z 覆盖 [%.1f, %.1f]（尖端应=182.0）' % (159.5 - max(ys), 159.5 - min(ys)))

# 抓手（X>50）位置复核
grip_z = [159.5 - p[1] for t in tris_out for p in t[1:] if p[0] > 50]
if grip_z:
    print('  侧向抓手 world z ∈ [%.1f, %.1f]（应在把手端 ~167.5..182）' % (min(grip_z), max(grip_z)))

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

ok_all = True
for link in range(1, 7):
    ok = RDK.setCollisionActivePair(1, robot, item, link, 0)
    ok_all = ok_all and (ok == 1)
print('自碰对 links1-6 全部建立 =', ok_all)
print('DONE（未保存工作站）')
