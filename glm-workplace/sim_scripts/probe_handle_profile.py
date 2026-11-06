# -*- coding: utf-8 -*-
# 只读：把手网格沿轴向(Y)分段的截面轮廓 —— 判断杆/把手块位置
import sys, io, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PATH = r'D:\mydata\glm-workplace\tools\handle_shortened_99.stl'
d = open(PATH, 'rb').read()
n = struct.unpack_from('<I', d, 80)[0]
pts = []
off = 84
for i in range(n):
    base = off + i * 50
    for k in range(3):
        vi = base + 12 + k * 12
        pts.append(struct.unpack_from('<3f', d, vi))

# 沿 Y 每 10mm 一段：X/Z 范围（顶点数）
Y0, Y1 = 55.0, 165.0
step = 10.0
y = Y0
print('局部Y段 → 世界z = 159.5 - Y （法兰 z=0，tip=z大）')
while y < Y1:
    sel = [p for p in pts if y <= p[1] < y + step]
    if sel:
        xs = [p[0] for p in sel]; zs = [p[2] for p in sel]
        print('Y[%6.1f,%6.1f) z≈[%5.1f,%5.1f]  n=%4d  X[%7.2f,%7.2f]  Z2[%6.2f,%6.2f]' % (
            y, y + step, 159.5 - (y + step), 159.5 - y, len(sel),
            min(xs), max(xs), min(zs), max(zs)))
    else:
        print('Y[%6.1f,%6.1f)  (空)' % (y, y + step))
    y += step
