# -*- coding: utf-8 -*-
"""v14w13：坑深修正——连接件顶坑底（止口深7mm） ⇒ 工具 106→99，网格同步。
网格手术2（源 handle_shortened_106.stl）：
  ①整体向法兰平移7（本地 y += 7，等效 Z -= 7）——反映"装进坑里、整体坐深7"；
  ②把 Z<0（原坑内段）顶点压平到 Z=0——坑内材料不建模（在机器人实体内部，
    建了反而与法兰网格假碰撞）。
  ⇒ 网格跨度 Z∈[0,99]，柄尖=99 与 PoseTool=99 一致。
站内替换：删旧→AddFile→parent=机器人、pose=identity、GeometryPose原值、名 门把手_bs1、
自碰对 links1-6 重建。不保存工作站。"""
import sys, io, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT
from robodk.robomath import Fanuc_2_Pose, Pose_2_Fanuc, eye

SRC = r'D:\mydata\glm-workplace\tools\handle_shortened_106.stl'
OUT = r'D:\mydata\glm-workplace\tools\handle_shortened_99.stl'
NAME = '门把手_bs1'
DEPTH = 7.0
TOOL_NEW = 99.0

# ---- 网格手术2 ----
d = open(SRC, 'rb').read()
n = struct.unpack_from('<I', d, 80)[0]
buf = bytearray(d)
clamped = 0
off = 84
for i in range(n):
    base = off + i * 50
    for k in range(3):
        vi = base + 12 + k * 12
        x, y, z = struct.unpack_from('<3f', buf, vi)
        y2 = y + DEPTH            # 整体平移：Z -> Z-7
        if 159.5 - y2 < 0.0:      # Z<0（坑内）→ 压平到 Z=0
            y2 = 159.5
            clamped += 1
        struct.pack_into('<3f', buf, vi, x, y2, z)
open(OUT, 'wb').write(buf)
# 校验跨度
off = 84
zs = []
for i in range(n):
    v = struct.unpack_from('<12f', buf, off)
    for k in range(3):
        zs.append(159.5 - (v[4 + 3 * k] + 0.0))   # y 已改，直接用 buf 内值
    off += 50
# 上面重复读的是改后 y——直接重解析
off = 84
zs = []
for i in range(n):
    v = struct.unpack_from('<12f', buf, off)
    for k in range(3):
        zs.append(159.5 - v[4 + 3 * k])
    off += 50
print('手术2完成：%s（%d 三角，压平顶点 %d，Z 跨度 [%.3f, %.3f]）' % (
    OUT, n, clamped, min(zs), max(zs)))
assert abs(max(zs) - TOOL_NEW) < 0.01, '柄尖不是99'

# ---- 工具 ----
RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
robot.setPoseTool(Fanuc_2_Pose([0.0, 0.0, TOOL_NEW, 0.0, 0.0, 0.0]))
t = Pose_2_Fanuc(robot.PoseTool())
print('PoseTool =', ['%.3f' % v for v in t])
assert abs(t[2] - TOOL_NEW) < 1e-9

# ---- 站内网格替换 ----
old = RDK.Item(NAME)
assert old.Valid()
old.Delete()
item = RDK.AddFile(OUT)
item.setParent(robot)
if any(abs(v) > 1e-9 for v in item.Pose().Pos()):
    item.setPose(eye(4))
item.setName(NAME)
item.setGeometryPose(Fanuc_2_Pose([0.0, 0.0, 159.5, -90.0, 0.0, 0.0]))
item.setVisible(True)
ok_pairs = True
for link in range(1, 7):
    ok_pairs = ok_pairs and (RDK.setCollisionActivePair(1, robot, item, link, 0) == 1)
print('站内替换: %s parent=%s 自碰对=%s' % (item.Name(), item.Parent().Name(), ok_pairs))
print('DONE（未保存工作站）')
