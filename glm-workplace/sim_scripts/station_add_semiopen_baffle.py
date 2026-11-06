# -*- coding: utf-8 -*-
"""站内新增「半封闭开口」挡板 = 三块独立薄板（不接触圆柱），一个网格对象。
v8（2026-10-14）：撤回 v6 的 +z50 —— 挡板 z 复原：上板 [760,780]→[710,730]、
  侧板 [50,760]→[0,710]、下板 [30,50]→[-20,0]；x 延长（上/下板 ±215）与 y 保留。
v7：上/下板 x∈[-215,215]（总长430）。v6：+z50（已撤回）。
v5：y 近端面 = 圆柱中心平面 y=-926。v2 起镜像开口朝 +x：
  平面定义（距圆柱中心 (0,-926,300) 的指定距离）：
    上板：⊥z，平面 z=710（中心+410）→ 板体 z∈[710, 730]
    侧板：⊥x，平面 x=-215 → 板体 x∈[-235, -215]
    下板：⊥z，平面 z=0（中心-300）→ 板体 z∈[-20, 0]
  三板共用 y∈[-926, -1226]；上/下板 x∈[-215, 215]；侧板 z∈[0,710]。
顶点烘焙基座坐标：AddFile 后 pose=identity、parent=Dobot CR5 Base。
名称登记进宏障碍物元组（精确名）；同名已存在时先删后建（幂等替换）。
"""
import sys, io, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import Robolink, ITEM_TYPE_OBJECT, ITEM_TYPE_ROBOT

NAME = '挡板_半封闭3面'
STL_OUT = r'D:\mydata\glm-workplace\tools\baffle_semiopen_3face_y300.stl'
Y0, Y1 = -926.0, -1226.0   # v5 起：近端面 = 圆柱中心平面 y=-926，向 -y 延 300

# 三块板的 AABB（基座坐标，v8：z 复原 + 保留 v7 的 x 延长）
BOXES = [
    (-215.0, 215.0, Y0, Y1, 710.0, 730.0),    # 上板（中心+410，x 总长430）
    (-235.0, -215.0, Y0, Y1, 0.0, 710.0),     # 侧板（左）
    (-215.0, 215.0, Y0, Y1, -20.0, 0.0),      # 下板（中心-300，x 总长430）
]

def box_tris(x0, x1, y0, y1, z0, z1):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    faces = [
        ((0, 0, -1), 0, 2, 1), ((0, 0, -1), 0, 3, 2),
        ((0, 0, 1), 4, 5, 6), ((0, 0, 1), 4, 6, 7),
        ((0, -1, 0), 0, 1, 5), ((0, -1, 0), 0, 5, 4),
        ((0, 1, 0), 3, 7, 6), ((0, 1, 0), 3, 6, 2),
        ((-1, 0, 0), 0, 4, 7), ((-1, 0, 0), 0, 7, 3),
        ((1, 0, 0), 1, 2, 6), ((1, 0, 0), 1, 6, 5),
    ]
    return [((n), v[a], v[b], v[c]) for n, a, b, c in faces]

tris = []
for bb in BOXES:
    tris.extend(box_tris(*bb))
buf = bytearray(b'\x00' * 80 + struct.pack('<I', len(tris)))
for nrm, a, b, c in tris:
    buf += struct.pack('<12fH', *nrm, *a, *b, *c, 0)
open(STL_OUT, 'wb').write(buf)
print('已生成 %s（%d 三角形 = 3 板 × 12）' % (STL_OUT, len(tris)))

RDK = Robolink()
old = RDK.Item(NAME, ITEM_TYPE_OBJECT)
if old.Valid():
    old.Delete()
    print('已删除旧同名对象（幂等替换）:', NAME)

base = RDK.Item('Dobot CR5 Base')
assert base.Valid(), '未找到 Dobot CR5 Base'
item = RDK.AddFile(STL_OUT)
item.setParent(base)
item.setName(NAME)
item.setVisible(True)
print('AddFile ->', item.Name(), 'valid=', item.Valid())

robot = RDK.Item('', ITEM_TYPE_ROBOT)
ok = RDK.setCollisionActivePair(1, robot, item, 0, 0)
print('碰撞配对 =', ok)

final = RDK.Item(NAME, ITEM_TYPE_OBJECT)
p = final.Pose().Pos()
print('回读: name=%s valid=%s parent=%s pose=(%.1f,%.1f,%.1f)' % (
    final.Name(), final.Valid(), final.Parent().Name(), p[0], p[1], p[2]))
print('DONE（未保存工作站）')
