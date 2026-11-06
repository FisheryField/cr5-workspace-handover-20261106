#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""判定 bs1.stp 极端点归属：真实几何顶点 vs B样条控制点。"""
import re, io

P = r"D:\mydata\working things\dobot_arm\2025.12\2025.12\bs1.stp"
txt = io.open(P, encoding="utf-8", errors="replace").read()

pts = {}
for m in re.finditer(r"#(\d+)\s*=\s*CARTESIAN_POINT\([^,]*,\s*\(([^)]*)\)\)", txt):
    try:
        pts[int(m.group(1))] = [float(x) for x in m.group(2).split(",")]
    except ValueError:
        pass

# 找出极端点 id
extremes = []
for pid, p in pts.items():
    if len(p) != 3:
        continue
    if p[0] < -50 or p[1] > 80 or p[1] < -5:
        extremes.append((pid, p))
print("极端点数:", len(extremes))

# 每个极端点被谁引用
id_set = {pid for pid, _ in extremes}
for pid, p in sorted(extremes, key=lambda t: t[1][0]):
    users = []
    for m in re.finditer(r"#(\d+)\s*=\s*([A-Z_0-9]+)\(([^;]*?)\)", txt):
        body = m.group(3)
        if "#%d" % pid in re.findall(r"#\d+", body):
            users.append(m.group(2))
    from collections import Counter
    c = Counter(users)
    print("  point #%d (%8.2f,%8.2f,%8.2f) 被 %s 引用" % (pid, p[0], p[1], p[2], dict(c)))

# 同时确认：真实顶点里 X 最大/最小、Y 最大 的点长什么样
vids = set(int(m.group(1)) for m in re.finditer(r"VERTEX_POINT\([^,]*,\s*#(\d+)\)", txt))
vp = [(i, pts[i]) for i in vids if i in pts]
print()
print("== 真实顶点极值 ==")
for i, p in sorted(vp, key=lambda t: -t[1][0])[:4]:
    print("  max-X #%d (%.2f, %.2f, %.2f)" % (i, p[0], p[1], p[2]))
for i, p in sorted(vp, key=lambda t: t[1][0])[:4]:
    print("  min-X #%d (%.2f, %.2f, %.2f)" % (i, p[0], p[1], p[2]))
for i, p in sorted(vp, key=lambda t: -t[1][1])[:4]:
    print("  max-Y #%d (%.2f, %.2f, %.2f)" % (i, p[0], p[1], p[2]))
