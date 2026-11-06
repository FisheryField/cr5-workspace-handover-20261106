#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在 TxPDO 映像里按【数值】搜主控读到的那一项：
   主控显示 J2 = 365.3275°  ⇒  counts = 365.3275 / SCALE
   gActualPosition J2 = 243.2175° ⇒ counts 也一并搜
   找到匹配的 32 位字段 ⇒ 那就是主控用的对象。"""
import io
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\workspace\data\txpdo_73000000_1741.bin'
d = io.open(P, 'rb').read()
BASE = 0x73000000
SCALE = 360.0 / (20000.0 * 101.0)

targets = {
    '主控显示 J2 = 365.3275°': 365.3275,
    'gActualPosition J2 = 243.2175°': 243.2175,
    '主控显示 J1 = 10.7583°': 10.7583,
    'gActual J1 = 40.1315°': 40.1315,
}

print('SCALE = %.6e 度/count' % SCALE)
print('')
for label, deg in targets.items():
    cnt = int(round(deg / SCALE))
    print('=== %s  ⇒ counts ≈ %d (0x%08X) ===' % (label, cnt, cnt & 0xFFFFFFFF))
    for signed in (True, False):
        pat = struct.pack('<i' if signed else '<I', cnt if signed else (cnt & 0xFFFFFFFF))
        hits = []
        i = d.find(pat)
        while i >= 0 and len(hits) < 8:
            hits.append(i)
            i = d.find(pat, i + 1)
        print('   %s 命中 %d 处: %s' % ('有符号' if signed else '无符号', len(hits),
                                        ' '.join('0x%05X' % h for h in hits)))
    # 允许 ±3 counts 的误差
    loose = []
    for off in range(0, len(d) - 4):
        v = struct.unpack_from('<i', d, off)[0]
        if abs(v - cnt) <= 3:
            loose.append((off, v))
    print('   容差±3 命中 %d 处: %s' % (len(loose),
                                        ' '.join('0x%05X(%d)' % (o, v) for o, v in loose[:10])))
    print('')
