#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""精算 bs1.stp：只取 VERTEX_POINT 引用的真实顶点求包围盒；圆半径参与极值；并查 .rdk 中缩放。"""
import re, io, struct, zlib

P = r"D:\mydata\working things\dobot_arm\2025.12\2025.12\bs1.stp"
txt = io.open(P, encoding="utf-8", errors="replace").read()

# 建立 id -> point 映射
pts = {}
for m in re.finditer(r"#(\d+)\s*=\s*CARTESIAN_POINT\([^,]*,\s*\(([^)]*)\)\)", txt):
    try:
        pts[int(m.group(1))] = [float(x) for x in m.group(2).split(",")]
    except ValueError:
        pass

# VERTEX_POINT 引用的点 = 真实几何顶点
vids = set()
for m in re.finditer(r"VERTEX_POINT\([^,]*,\s*#(\d+)\)", txt):
    vids.add(int(m.group(1)))
vp = [pts[i] for i in vids if i in pts and len(pts[i]) == 3]
print("真实顶点数:", len(vp))
if vp:
    xs=[p[0] for p in vp]; ys=[p[1] for p in vp]; zs=[p[2] for p in vp]
    print("顶点包围盒: %.3f x %.3f x %.3f mm" % (max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs)))
    print("范围: X[%.2f,%.2f] Y[%.2f,%.2f] Z[%.2f,%.2f]" % (min(xs),max(xs),min(ys),max(ys),min(zs),max(zs)))

# 圆：中心+半径（极值可超出顶点，比如完整圆柱侧面无顶点在圆周上）
print()
print("== 圆（半径排序，前 12 大）==")
circles = []
for m in re.finditer(r"#(\d+)\s*=\s*CIRCLE\([^,]*,\s*#(\d+),([\d.]+)\)", txt):
    cid, cpid, r = int(m.group(1)), int(m.group(2)), float(m.group(3))
    if cpid in pts:
        circles.append((r, pts[cpid]))
for r, c in sorted(circles, key=lambda t: -t[0])[:12]:
    print("  R=%7.3f  center=(%.2f, %.2f, %.2f)" % (r, c[0], c[1], c[2]))

# .rdk 中 bs1 路径附近找缩放（Scale 常以 float32 数组出现）
print()
print("== .rdk bs1 引用附近的可疑参数 ==")
raw = open(r"D:\mydata\working things\dobot_arm\RoboDK files 2\2026-9-7.rdk", "rb").read()
data = zlib.decompress(raw[4:])
h = data.find("bs1.stp".encode("utf-16-le"))
print("path hit at:", h)
# 缩放一般是三个相邻 float32 ≈1.0；在前后 512 字节内找 float32 数组
import struct as st
lo, hi = max(0, h-600), h+600
vals = []
for off in range(lo, hi-12, 4):
    f3 = st.unpack("<3f", data[off:off+12])
    if all(0.01 < v < 100 for v in f3):
        vals.append((off-h, f3))
for d, f3 in vals[:20]:
    print("  off%+d: %.4f %.4f %.4f" % (d, *f3))
