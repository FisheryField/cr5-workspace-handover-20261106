# -*- coding: utf-8 -*-
"""把手网格手术 182→126（2026-10-24）：最终实测法兰→末端=126，网格 182 属高报 56mm。
截断 handle_rod_182_v2.stl 于 z_tool=126（y_stl≥33.5 保留），输出 handle_rod_126.stl，
站内替换门把手_bs1（GeometryPose 不变），重建自碰对。之后滚轮按 1mm 规则摆位。"""
import sys, io, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT
from robodk.robomath import Fanuc_2_Pose, Pose_2_Fanuc, eye

SRC = r'D:\mydata\glm-workplace\tools\handle_rod_182_v2.stl'
OUT = r'D:\mydata\glm-workplace\tools\handle_rod_126.stl'
NAME = '门把手_bs1'
Y_KEEP_MIN = 33.5   # z_tool = 159.5 - y_stl ≤ 126  ⇔  y_stl ≥ 33.5

d = open(SRC, 'rb').read()
n = struct.unpack_from('<I', d, 80)[0]
kept, dropped = [], 0
off = 84
for i in range(n):
    rec = d[off + i * 50: off + i * 50 + 50]
    vals = struct.unpack_from('<12f', rec, 0)
    ys = (vals[4], vals[7], vals[10])   # 三个顶点的 y_stl
    if min(ys) >= Y_KEEP_MIN - 1e-6:
        kept.append(rec)
    else:
        dropped += 1

buf = bytearray(84 + 50 * len(kept))
hdr = b'handle_rod_126 trunc wp=126 v14w40-era'
buf[0:80] = (hdr + b' ' * 80)[:80]
struct.pack_into('<I', buf, 80, len(kept))
for i, rec in enumerate(kept):
    buf[84 + i * 50: 84 + i * 50 + 50] = rec
open(OUT, 'wb').write(bytes(buf))

# 包围盒复核（局部 → world z）
xs, ys, zs = [], [], []
for i in range(len(kept)):
    vals = struct.unpack_from('<12f', bytes(kept[i]), 0)
    for k in (3, 6, 9):
        xs.append(vals[k]); ys.append(vals[k + 1]); zs.append(vals[k + 2])
print('保留三角 %d / 丢弃 %d' % (len(kept), dropped))
print('局部 bbox Y[%.2f,%.2f] → world z[%.1f, %.1f]（尖端应=126.0）' % (
    min(ys), max(ys), 159.5 - max(ys), 159.5 - min(ys)))

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
print('站内替换完成: parent=%s' % item.Parent().Name())
ok_all = True
for link in range(1, 7):
    ok = RDK.setCollisionActivePair(1, robot, item, link, 0)
    ok_all = ok_all and (ok == 1)
print('自碰对 links1-6 =', ok_all)

# ---- 滚轮 1mm 规则位：表面 y=-688 ⇒ 中心 y=-838（z=460 不动）----
cyl = RDK.Item('磨砂圆柱_R150_H50')
cp = Pose_2_Fanuc(cyl.Pose())
print('滚轮 y: %.1f -> -838.0' % cp[1])
cyl.setPose(Fanuc_2_Pose([cp[0], -838.0, cp[2], cp[3], cp[4], cp[5]]))
cp2 = Pose_2_Fanuc(cyl.Pose())
print('滚轮现在 = (%.1f, %.1f, %.1f)  赤道面 y=%.1f（P2 y=-687，间隙 1.0mm）' % (
    cp2[0], cp2[1], cp2[2], cp2[1] + 150))
print('DONE（未保存工作站）')
