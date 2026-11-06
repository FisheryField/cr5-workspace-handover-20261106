#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按实际版本字落点手工解码每轴 TxPDO 块（D8 布局）。"""
import io
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\workspace\data\txpdo_73000000_1741.bin'
d = io.open(P, 'rb').read()
BASE = 0x73000000

# 版本字在块内偏移 35（J1..J5 布局）
VER_OFF = 35
ENTRIES = [
    ('0x6041 STATUSWORD', 0, 2),
    ('0x6061 modes', 2, 1),
    ('0x6064 pos actual', 3, 4),
    ('0x606C vel actual', 7, 4),
    ('0x6077 torque actual', 11, 2),
    ('0x6075 rated current', 13, 4),
    ('0x6076 rated torque', 17, 4),
    ('0x603F ERROR CODE', 21, 2),
    ('0x6079 dc link V', 23, 4),
    ('0x6078 current actual', 27, 2),
    ('0x5000:07 VERSION', 35, 2),
    ('0x6062 (target v?)', 53, 4),
]

hits = []
i = d.find(b'\xd8\x32')
while i >= 0:
    hits.append(i)
    i = d.find(b'\xd8\x32', i + 1)

names = ['J1', 'J2', 'J3', 'J4', 'J5', 'J6']
print('版本字命中 %d 处；按命中位置反推块起点（命中 − %d）' % (len(hits), VER_OFF))
print('')
for k, h in enumerate(hits):
    start = h - VER_OFF
    nm = names[k] if k < len(names) else 'J?'
    print('=== %s  块起点 = 0x%05X (绝对 0x%08X) 版本字=0x%04X ==='
          % (nm, start, BASE + start, struct.unpack_from('<H', d, h)[0]))
    if start < 0 or start + 57 > len(d):
        print('   （越界，跳过）')
        continue
    for label, off, width in ENTRIES:
        pos = start + off
        if pos + width > len(d):
            continue
        if width == 2:
            v = struct.unpack_from('<H', d, pos)[0]
            sv = struct.unpack_from('<h', d, pos)[0]
            print('   +%-3d %-22s = 0x%04X  (%d / signed %d)' % (off, label, v, v, sv))
        elif width == 1:
            v = d[pos]
            print('   +%-3d %-22s = 0x%02X  (%d)' % (off, label, v, v))
        else:
            v = struct.unpack_from('<i', d, pos)[0]
            print('   +%-3d %-22s = %d  (0x%08X)' % (off, label, v, v & 0xFFFFFFFF))
    print('')
