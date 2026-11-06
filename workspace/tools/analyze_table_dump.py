#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分析 0x32c000 表区与 0x75600000 应用数据区：
   找版本字所在的 24 字节记录结构，并搜关节位置值（int32 / float32 / float64）。"""
import io
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
SCALE = 360.0 / (20000.0 * 101.0)
FILES = [
    (r'D:\mydata\workspace\data\table_32c000.bin', 0x32c000, '表区 0x32c000'),
    (r'D:\mydata\workspace\data\app_75600000.bin', 0x75600000, '应用数据 0x75600000'),
]
POS = {'J1': 36975, 'J2': 65421, 'J3': 4526, 'J4': 21419, 'J5': 47702, 'J6': 60374}

for path, base, label in FILES:
    d = io.open(path, 'rb').read()
    print('=' * 70)
    print('%s  文件 %d 字节  (base 0x%08X)' % (label, len(d), base))
    print('=' * 70)

    # 1) 版本字命中与周边
    hits = []
    i = d.find(b'\xd8\x32')
    while i >= 0:
        hits.append(i)
        i = d.find(b'\xd8\x32', i + 1)
    print('  版本字 0x32D8 命中 %d 处: %s' % (len(hits), ' '.join('0x%05X' % h for h in hits[:12])))
    if hits:
        h = hits[len(hits) // 2]
        lo = max(0, h - 24)
        hi = min(len(d), h + 40)
        print('  以中间那处 (0x%05X) 为中心，前后各 24/40 字节：' % h)
        for off in range(lo, hi, 8):
            row = d[off:off + 8]
            v32 = struct.unpack_from('<i', d, off)[0] if off + 4 <= len(d) else 0
            v32u = struct.unpack_from('<I', d, off)[0] if off + 4 <= len(d) else 0
            f32 = struct.unpack_from('<f', d, off)[0] if off + 4 <= len(d) else 0
            mark = '  <<< 版本字' if off <= h < off + 8 else ''
            print('    0x%05X  %s   int32=%-10d u32=%-10d f32=%g%s'
                  % (off, row.hex(' '), v32, v32u, f32, mark))
    print('')

    # 2) 搜关节位置值
    for name, cnt in POS.items():
        f_int = []
        pat = struct.pack('<i', cnt)
        i = d.find(pat)
        while i >= 0 and len(f_int) < 6:
            f_int.append(i)
            i = d.find(pat, i + 1)
        f_flt = []
        patf = struct.pack('<f', cnt * SCALE)
        i = d.find(patf)
        while i >= 0 and len(f_flt) < 6:
            f_flt.append(i)
            i = d.find(patf, i + 1)
        print('  %s  counts=%d   int32命中 %s   float32(%.4f°)命中 %s'
              % (name, cnt,
                 ' '.join('0x%05X' % o for o in f_int) or '-',
                 cnt * SCALE,
                 ' '.join('0x%05X' % o for o in f_flt) or '-'))
    print('')
