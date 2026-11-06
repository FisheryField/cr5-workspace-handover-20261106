# -*- coding: utf-8 -*-
"""门把手模型手术 v2：连接件缩短 53.629mm 并替换站内网格（配合 v14w11 工具=106）。
- STL 手术：远端（本地 y≤105.871）平移 +53.629，近法兰段保留 ⇒ Z 跨度 [0,159.5]→[0,105.871]。
- 站内替换：删旧 → AddFile → parent=机器人、pose=identity、GeometryPose 原值、名 门把手_bs1。
- 碰撞：①显式建立 robot↔把手 links1-6 自碰对；②障碍物对由宏 v14w12 的【按名并入】循环
  负责（新项类型为 OBJECT，不在 TOOL 过滤器里）。
不保存工作站。"""
import sys, io, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT
from robodk.robomath import Fanuc_2_Pose, Pose_2_Fanuc, eye

SRC = r'D:\mydata\glm-workplace\tools\handle_export_test.stl'
OUT = r'D:\mydata\glm-workplace\tools\handle_shortened_106.stl'
NAME = '门把手_bs1'
DELTA = 53.629
Y_KEEP = 159.5 - DELTA   # 105.871

# ---- STL 手术 ----
d = open(SRC, 'rb').read()
n = struct.unpack_from('<I', d, 80)[0]
buf = bytearray(d)
off = 84
moved = 0
for i in range(n):
    base = off + i * 50
    for k in range(3):
        vi = base + 12 + k * 12
        x, y, z = struct.unpack_from('<3f', buf, vi)
        if y <= Y_KEEP:
            struct.pack_into('<3f', buf, vi, x, y + DELTA, z)
            moved += 1
open(OUT, 'wb').write(buf)
print('STL 手术完成：%s（%d 三角形，移动顶点 %d）' % (OUT, n, moved))

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
print('站内替换: name=%s type=%s parent=%s' % (item.Name(), item.Type(), item.Parent().Name()))
print('  pose pos=', ['%.3f' % v for v in item.Pose().Pos()],
      ' GeometryPose=', ['%.3f' % v for v in Pose_2_Fanuc(item.GeometryPose())])

# ---- 自碰对（links1-6 ↔ 把手）----
ok_all = True
for link in range(1, 7):
    ok = RDK.setCollisionActivePair(1, robot, item, link, 0)
    ok_all = ok_all and (ok == 1)
print('自碰对 links1-6 全部建立 =', ok_all)
print('DONE（未保存工作站；障碍物对等待宏 v14w12 按名循环生效）')
