# -*- coding: utf-8 -*-
"""站内新增挡板（只加几何，不保存工作站）。
几何（基座 Dobot CR5 Base 坐标系，与用户口述一致）：
  x ∈ [0, 215]      （圆柱中心线向右 215，左侧不加——路径默认不从左边走）
  y ∈ [-956, -976]  （从平面 y=-956 向 y 负方向延伸 20mm 薄板）
  z ∈ [0, 710]      （圆柱中心 z=300：上侧 410 → 710，下侧 300 → 0）
顶点直接烘焙在基座坐标系：AddFile 后 pose=identity、parent=Dobot CR5 Base。
名称 '挡板_215x710x20' 将登记进宏的障碍物元组（精确名匹配）。
"""
import sys, io, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import Robolink, ITEM_TYPE_OBJECT, ITEM_TYPE_ROBOT

NAME = '挡板_215x710x20'
STL_OUT = r'D:\mydata\glm-workplace\tools\baffle_215x710x20.stl'
X0, X1 = 0.0, 215.0
Y0, Y1 = -956.0, -976.0     # 近面 y=-956，向 -y 延伸
Z0, Z1 = 0.0, 710.0

def write_box_stl(path, x0, x1, y0, y1, z0, z1):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    faces = [  # (normal, a, b, c) 外法线
        ((0, 0, -1), 0, 2, 1), ((0, 0, -1), 0, 3, 2),
        ((0, 0, 1), 4, 5, 6), ((0, 0, 1), 4, 6, 7),
        ((0, -1, 0), 0, 1, 5), ((0, -1, 0), 0, 5, 4),
        ((0, 1, 0), 3, 7, 6), ((0, 1, 0), 3, 6, 2),
        ((-1, 0, 0), 0, 4, 7), ((-1, 0, 0), 0, 7, 3),
        ((1, 0, 0), 1, 2, 6), ((1, 0, 0), 1, 6, 5),
    ]
    buf = bytearray(b'\x00' * 80 + struct.pack('<I', len(faces)))
    for nrm, a, b, c in faces:
        buf += struct.pack('<12fH', *nrm, *v[a], *v[b], *v[c], 0)
    open(path, 'wb').write(buf)
    return len(faces)

ntri = write_box_stl(STL_OUT, X0, X1, Y0, Y1, Z0, Z1)
print('已生成 %s（%d 三角形）' % (STL_OUT, ntri))

RDK = Robolink()
dup = [x for x in RDK.ItemList() if (x if isinstance(x, str) else x.Name()) == NAME]
if dup:
    print('站内已存在同名对象，中止（先手动删除再跑）:', NAME)
    sys.exit(1)

base = RDK.Item('Dobot CR5 Base')
assert base.Valid(), '未找到 Dobot CR5 Base'

item = RDK.AddFile(STL_OUT)
print('AddFile ->', item.Name(), 'valid=', item.Valid())
item.setParent(base)          # 顶点已是基座坐标 ⇒ pose 保持 identity
item.setName(NAME)
item.setVisible(True)

robot = RDK.Item('', ITEM_TYPE_ROBOT)
ok = RDK.setCollisionActivePair(1, robot, item, 0, 0)
print('碰撞配对 setCollisionActivePair(robot, baffle) =', ok)

final = RDK.Item(NAME, ITEM_TYPE_OBJECT)
p = final.Pose().Pos()
print('回读: name=%s valid=%s parent=%s pose=(%.1f,%.1f,%.1f)' % (
    final.Name(), final.Valid(), final.Parent().Name(), p[0], p[1], p[2]))
print('DONE：挡板已加入站内（未保存工作站）')
