#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解析 bs1.stp：全部 CARTESIAN_POINT 求包围盒；读 PRODUCT 名称；统计几何元素。"""
import re, io

P = r"D:\mydata\working things\dobot_arm\2025.12\2025.12\bs1.stp"
txt = io.open(P, encoding="utf-8", errors="replace").read()

# PRODUCT / PART 名称
print("== PRODUCT 名称 ==")
for m in re.finditer(r"PRODUCT\('([^']*)'", txt):
    print("  ", m.group(1))
for m in re.finditer(r"PRODUCT_DEFINITION_SHAPE|NEXT_ASSEMBLY_USAGE_OCCURRENCE\('([^']*)'", txt):
    if m.group(1):
        print("  NAUO:", m.group(1))

# 全部笛卡尔点
pts = []
for m in re.finditer(r"CARTESIAN_POINT\([^,]*,\s*\(([^)]*)\)\)", txt):
    try:
        v = [float(x) for x in m.group(1).split(",")]
        if len(v) == 3:
            pts.append(v)
    except ValueError:
        pass
print()
print("CARTESIAN_POINT 数量:", len(pts))
if pts:
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; zs = [p[2] for p in pts]
    dx, dy, dz = max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs)
    print("包围盒: X %.3f  Y %.3f  Z %.3f  (STEP 单位通常 mm)" % (dx, dy, dz))
    print("范围: X[%.2f, %.2f] Y[%.2f, %.2f] Z[%.2f, %.2f]" % (min(xs),max(xs),min(ys),max(ys),min(zs),max(zs)))

# 单位声明
print()
print("== 单位 ==")
for m in re.finditer(r"SI_UNIT\([^)]*\)|CONVERSION_BASED_UNIT\('([^']*)'[^)]*\)", txt):
    print("  ", m.group(0)[:80])

# 几何元素统计
print()
print("== 元素统计 ==")
for kw in ["CYLINDRICAL_SURFACE", "TOROIDAL_SURFACE", "B_SPLINE_SURFACE", "PLANE(", "ADVANCED_FACE", "CLOSED_SHELL", "MANIFOLD_SOLID_BREP", "CIRCLE(", "B_SPLINE_CURVE"]:
    n = txt.count(kw)
    if n:
        print("  %-22s %d" % (kw, n))
