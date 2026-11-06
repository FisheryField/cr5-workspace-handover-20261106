# -*- coding: utf-8 -*-
"""站内场景：圆柱 + 挡板 整体后移（远离基座）82mm —— 用户指令 2026-10-20。
- 统一 pose.y −82（世界 y 方向，远离机械臂）。
- 打印移动前后世界包围盒（STL 局部顶点 × item.Pose()，父级=Base 即站内坐标）。
- 不保存工作站。
"""
import sys, io, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from robodk.robolink import Robolink
from robodk.robomath import Pose_2_Fanuc, Fanuc_2_Pose, transl, rotz  # noqa
from robodk.robomath import Mat

RDK = Robolink()
DY = -82.0
NAMES = ['磨砂圆柱_R150_H50', '挡板_半封闭3面']


def item_world_bbox(it):
    # 从站内导出 STL 顶点？简化：用 AddFile 前已知——直接取 GeometryPose? 不可靠。
    # 采用：临时导出网格文件读顶点（只读导出到 dump 目录）。
    import tempfile, os
    d = tempfile.mkdtemp(dir=r'D:\mydata\glm-workplace\sim_scripts\rdk_station_dump')
    p = os.path.join(d, 'bb.stl')
    it.Save(p)
    raw = open(p, 'rb').read()
    n = struct.unpack_from('<I', raw, 80)[0]
    T = it.Pose()          # 相对父级(Base)：站内坐标
    m = T.rows             # list of 4 rows × 4 floats
    xs, ys, zs = [], [], []
    off = 84
    for i in range(n):
        base = off + i * 50
        for k in range(3):
            vi = base + 12 + k * 12
            x, y, z = struct.unpack_from('<3f', raw, vi)
            xs.append(m[0][0]*x + m[0][1]*y + m[0][2]*z + m[0][3])
            ys.append(m[1][0]*x + m[1][1]*y + m[1][2]*z + m[1][3])
            zs.append(m[2][0]*x + m[2][1]*y + m[2][2]*z + m[2][3])
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))


for name in NAMES:
    it = RDK.Item(name)
    assert it.Valid(), name
    p = Pose_2_Fanuc(it.Pose())
    bb0 = item_world_bbox(it)
    print('%s BEFORE pose=(%.1f,%.1f,%.1f, %.0f,%.0f,%.0f)' % (name, p[0], p[1], p[2], p[3], p[4], p[5]))
    print('   world bbox X[%.1f,%.1f] Y[%.1f,%.1f] Z[%.1f,%.1f]' % (bb0[0][0], bb0[0][1], bb0[1][0], bb0[1][1], bb0[2][0], bb0[2][1]))
    it.setPose(Fanuc_2_Pose([p[0], p[1] + DY, p[2], p[3], p[4], p[5]]))
    p2 = Pose_2_Fanuc(it.Pose())
    bb1 = item_world_bbox(it)
    print('   AFTER  pose=(%.1f,%.1f,%.1f, %.0f,%.0f,%.0f)' % (p2[0], p2[1], p2[2], p2[3], p2[4], p2[5]))
    print('   world bbox X[%.1f,%.1f] Y[%.1f,%.1f] Z[%.1f,%.1f]' % (bb1[0][0], bb1[0][1], bb1[1][0], bb1[1][1], bb1[2][0], bb1[2][1]))

print('DONE（后移 %.0fmm，未保存工作站）' % abs(DY))
