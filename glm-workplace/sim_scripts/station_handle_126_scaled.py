# -*- coding: utf-8 -*-
"""把手网格手术：轴向压缩 182→126（s=126/182），形状完整可见，尖端=工作点126。
源=handle_rod_182_v2.stl → handle_rod_126_scaled.stl；站内替换；滚轮保持-838。"""
import sys, io, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT
from robodk.robomath import Fanuc_2_Pose, Pose_2_Fanuc, eye

SRC = r'D:\mydata\glm-workplace\tools\handle_rod_182_v2.stl'
OUT = r'D:\mydata\glm-workplace\tools\handle_rod_126_scaled.stl'
NAME = '门把手_bs1'
S = 126.0 / 182.0
Y0 = 159.5   # z_tool = Y0 - y_stl

d = open(SRC, 'rb').read()
n = struct.unpack_from('<I', d, 80)[0]
buf = bytearray(84 + 50 * n)
buf[0:80] = (b'handle_rod_126_scaled axis-compress 182->126' + b' ' * 80)[:80]
struct.pack_into('<I', buf, 80, n)
ys_all = []
for i in range(n):
    vals = list(struct.unpack_from('<12f', d, 84 + i * 50))
    # 顶点 y_stl（下标4,7,10）→ z_tool' = (Y0-y)*S → y' = Y0 - z_tool'
    for k in (4, 7, 10):
        zt = (Y0 - vals[k]) * S
        vals[k] = Y0 - zt
        ys_all.append(vals[k])
    struct.pack_into('<12fH', buf, 84 + i * 50, *vals[:12], 0)
open(OUT, 'wb').write(bytes(buf))
zt_min = Y0 - max(ys_all)   # 最大 y_stl → 最小 z_tool
zt_max = Y0 - min(ys_all)
print('压缩后 world z ∈ [%.1f, %.1f]（尖端应=126.0）' % (zt_min, zt_max))

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
old = RDK.Item(NAME)
assert old.Valid()
old.Delete()
item = RDK.AddFile(OUT)
item.setParent(robot)
p = item.Pose()
if any(abs(v) > 1e-9 for v in p.Pos()) or Pose_2_Fanuc(p)[3] != 0:
    item.setPose(eye(4))
item.setName(NAME)
item.setGeometryPose(Fanuc_2_Pose([0.0, 0.0, 159.5, -90.0, 0.0, 0.0]))
item.setVisible(True)
ok_all = True
for link in range(1, 7):
    ok_all = ok_all and (RDK.setCollisionActivePair(1, robot, item, link, 0) == 1)
print('站内替换完成；自碰对 =', ok_all)
print('DONE')
