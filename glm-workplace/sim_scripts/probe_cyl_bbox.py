# -*- coding: utf-8 -*-
"""只读：测站内磨砂圆柱真实包围盒（定半径/中心），对齐贴合带与轨迹14 的 y。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import socket
socket.setdefaulttimeout(12)
from robodk import robolink

RDK = robolink.Robolink()
for nm in ('磨砂圆柱_R150_H50',):
    it = RDK.Item(nm)
    if not it.Valid():
        print(nm, '不存在')
        continue
    bb = it.BoundingBox()   # Mat 2x4 或 4x4
    try:
        rows = bb.rows if hasattr(bb, 'rows') else None
        vals = []
        rws = bb.tolist() if hasattr(bb, 'tolist') else [[bb[i, j] for j in range(4)] for i in range(bb.size(0))]
        xs, ys, zs = [], [], []
        for row in rws:
            for v in (row if isinstance(row, (list, tuple)) else [row]):
                pass
        # 直接取 8 角点常见布局：2x4（min/max 行）或 4x4
        flat = [float(v) for row in rws for v in (row if isinstance(row, (list, tuple)) else [row])]
        print(nm, 'bbox flat =', [round(v, 1) for v in flat])
    except Exception as e:
        print(nm, 'bbox 读取异常:', e)
print('DONE')
