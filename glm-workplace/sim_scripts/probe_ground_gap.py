# -*- coding: utf-8 -*-
"""只读探针：读站内 圆柱/地面/安装台 位姿，按 STL 局部包围盒 8 角点变换到基座系，
算圆柱底面到地面顶面的距离。不改对象、不碰关节、不保存工作站。
"""
from robodk.robolink import *
from robodk.robomath import *

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
if not robot.Valid():
    raise SystemExit('未找到机器人')

T_base_inv = invH(robot.Pose())  # station -> base

# 磁盘 STL 局部包围盒（sys 外已算好）
MESH_BBOX = {
    '磨砂圆柱_R150_H50': ((-150, 150), (-150, 150), (-25, 25)),      # cylinder_R150_H50.stl
    '地面_禁止穿越': ((-2000, 2000), (-2000, 2000), (-2080, -80)),   # ground_export.stl
}

def world_z_range(item, mesh_bbox):
    """网格局部 8 角点 -> GeometryPose -> 对象系 -> 基座系，返回 z 的 [min,max]。"""
    P = T_base_inv * item.Pose()
    G = item.GeometryPose()
    (x0, x1), (y0, y1), (z0, z1) = mesh_bbox
    zs = []
    for x in (x0, x1):
        for y in (y0, y1):
            for z in (z0, z1):
                p = G * [x, y, z]          # 局部 -> 对象系
                q = P * [p[0], p[1], p[2]]  # 对象系 -> 基座系
                zs.append(q[2])
    return min(zs), max(zs)

for name in ('安装台_650x650x80mm', '地面_禁止穿越', '磨砂圆柱_R150_H50', '挡板_半封闭3面'):
    it = RDK.Item(name, ITEM_TYPE_OBJECT)
    if not it.Valid():
        print(name, '=> MISSING')
        continue
    Pb = T_base_inv * it.Pose()
    print('%s:' % name)
    print('  基座系原点 = (%.3f, %.3f, %.3f)' % (Pb[0, 3], Pb[1, 3], Pb[2, 3]))
    if name in MESH_BBOX:
        z0, z1 = world_z_range(it, MESH_BBOX[name])
        print('  STL网格基座系 z 范围 = [%.3f, %.3f]' % (z0, z1))
        if name == '磨砂圆柱_R150_H50':
            cyl_bottom = z0
        elif name == '地面_禁止穿越':
            gnd_top = z1

if 'cyl_bottom' in dir() and 'gnd_top' in dir():
    print('RESULT 圆柱底面 z=%.3f  地面顶面 z=%.3f  间距=%.3f mm' % (cyl_bottom, gnd_top, cyl_bottom - gnd_top))
