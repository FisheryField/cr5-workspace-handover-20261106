#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在 TxPDO 映像里找版本字 0x32D8 / 0x3150 与各轴块的落点。"""
import io
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\workspace\data\txpdo_73000000_1741.bin'
d = io.open(P, 'rb').read()
print('dump 大小 = %d 字节 (base 0x73000000)' % len(d))

for name, pat in (('0x32D8 (D8)', b'\xd8\x32'), ('0x3150 (3.1.5.0)', b'\x50\x31')):
    hits = []
    i = d.find(pat)
    while i >= 0 and len(hits) < 40:
        hits.append(i)
        i = d.find(pat, i + 1)
    print('  %-16s 命中 %d 处  %s' % (name, len(hits),
                                     ' '.join('0x%05X' % h for h in hits[:20])))

# 打印非零区域概览
print('')
print('=== 非零字节密度（每 256 字节一段，标记有数据的段）===')
segs = []
for off in range(0, len(d), 256):
    chunk = d[off:off + 256]
    nz = sum(1 for b in chunk if b)
    if nz > 8:
        segs.append((off, nz))
print('  有数据的 256B 段数 =', len(segs))
for off, nz in segs[:24]:
    print('    0x%05X  非零 %3d/256' % (off, nz))

# 找连续的 0x6064 位置值（float 或 int 都可能）——先把前 512 字节按 u16/u32 打出来
print('')
print('=== 偏移 0x2600..0x2700 的 u16 视图（文档说 J1 块在 0x7300266C 附近）===')
for off in range(0x2600, min(0x2700, len(d)), 16):
    vals = struct.unpack_from('<8H', d, off)
    print('  0x%05X  %s' % (off, ' '.join('%04x' % v for v in vals)))
