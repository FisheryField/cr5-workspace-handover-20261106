# -*- coding: utf-8 -*-
# 只读：handle_shortened_99.stl 连通组件分析（按共享顶点合并），打印各组件 Y 范围
import sys, io, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PATH = r'D:\mydata\glm-workplace\tools\handle_shortened_99.stl'
d = open(PATH, 'rb').read()
n = struct.unpack_from('<I', d, 80)[0]

tris = []
verts = []
vmap = {}
def vid(x, y, z):
    k = (round(x, 4), round(y, 4), round(z, 4))
    i = vmap.get(k)
    if i is None:
        i = len(verts)
        vmap[k] = i
        verts.append(k)
    return i

off = 84
for i in range(n):
    base = off + i * 50
    v = struct.unpack_from('<9f', d, base + 12)
    a = vid(v[0], v[1], v[2]); b = vid(v[3], v[4], v[5]); c = vid(v[6], v[7], v[8])
    tris.append((a, b, c))

# union-find
par = list(range(len(verts)))
def find(a):
    while par[a] != a:
        par[a] = par[par[a]]
        a = par[a]
    return a
def uni(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        par[rb] = ra

for a, b, c in tris:
    uni(a, b); uni(b, c)

from collections import defaultdict
comp_verts = defaultdict(set)
for a, b, c in tris:
    for v in (a, b, c):
        comp_verts[find(v)].add(v)
comp_tris = defaultdict(int)
for a, b, c in tris:
    comp_tris[find(a)] += 1

print('组件数 =', len(comp_verts))
rows = []
for root, vs in comp_verts.items():
    ys = [verts[v][1] for v in vs]
    xs = [verts[v][0] for v in vs]
    zs = [verts[v][2] for v in vs]
    rows.append((min(ys), max(ys), comp_tris[root], min(xs), max(xs), min(zs), max(zs)))
rows.sort()
print('%-6s %-6s %-6s | X范围 | Z范围 | 三角 | world z 范围' % ('Ymin', 'Ymax', ''))
for ymin, ymax, nt, xmin, xmax, zmin, zmax in rows:
    print('Y[%7.2f,%7.2f]  X[%6.2f,%6.2f] Z2[%6.2f,%6.2f] tri=%4d  → z[%.1f, %.1f]' % (
        ymin, ymax, xmin, xmax, zmin, zmax, nt, 159.5 - ymax, 159.5 - ymin))
print('DONE')
