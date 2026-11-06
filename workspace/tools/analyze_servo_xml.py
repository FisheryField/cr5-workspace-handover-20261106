#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解剖 CR_Servo_ST_XML_V3.0.0.bin（2048 B）：结构、字符串、是否含 PDO 条目。"""
import re
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\workspace\data\official\pkg\CR_Servo_ST_XML_V3.0.0.bin'
d = open(P, 'rb').read()
print('文件 %d 字节' % len(d))
print('')
print('=== 前 256 字节 ===')
for i in range(0, min(256, len(d)), 16):
    row = d[i:i + 16]
    txt = ''.join(chr(b) if 32 <= b < 127 else '.' for b in row)
    print('  %04X  %-47s  %s' % (i, row.hex(' '), txt))

print('')
print('=== 可打印字符串（≥4 字符）===')
for m in re.finditer(rb'[\x20-\x7e]{4,}', d):
    print('  @%04X  %s' % (m.start(), m.group().decode('ascii', 'replace')))

print('')
print('=== 是否含 EtherCAT PDO 条目形态（u16 index + u8 sub + u8 bits）===')
hits = []
for off in range(0, len(d) - 4):
    idx, sub, bits = struct.unpack_from('<HBB', d, off)
    if idx in (0x1600, 0x1601, 0x1602, 0x1A00, 0x1A01, 0x1A02, 0x1C12, 0x1C13) or \
       (0x6000 <= idx <= 0x67FF and sub <= 0x20 and bits in (1, 2, 4, 8, 16, 32)):
        hits.append((off, idx, sub, bits))
for off, idx, sub, bits in hits[:40]:
    print('  @%04X  index=0x%04X sub=0x%02X bits=%d' % (off, idx, sub, bits))
print('  合计 %d 处候选' % len(hits))

print('')
print('=== 已知关节对象索引是否出现（0x6062/0x6063/0x6064/0x607A/0x5000）===')
for name, v in (('0x6062', 0x6062), ('0x6063', 0x6063), ('0x6064', 0x6064),
                ('0x607A', 0x607A), ('0x5000', 0x5000), ('0x1600', 0x1600), ('0x1A00', 0x1A00)):
    pat_le = struct.pack('<H', v)
    pat_be = struct.pack('>H', v)
    print('  %-7s LE %s (%d 处)   BE %s (%d 处)'
          % (name, pat_le.hex(), d.count(pat_le), pat_be.hex(), d.count(pat_be)))

print('')
print('=== 尾部 128 字节 ===')
for i in range(max(0, len(d) - 128), len(d), 16):
    row = d[i:i + 16]
    txt = ''.join(chr(b) if 32 <= b < 127 else '.' for b in row)
    print('  %04X  %-47s  %s' % (i, row.hex(' '), txt))
