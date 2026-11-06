#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在伺服固件里搜故障码 0x8612(34322) / 0x8481(33921) / 0x7180(29056)，
   并看它们是以什么形式存在的（指令立即数 / 半字表 / 字面量池），再反汇编周边。"""
import io
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SAMPLES = [
    (r'D:\mydata\workspace\data\servo_fw_samples\elf\v3150.bin', 0x08010000, '3.1.5.0'),
    (r'D:\mydata\workspace\data\servo_fw_samples\elf\v328d8.bin', 0x08010000, '3.2.D.8'),
]
CODES = {'0x8612 (给定超范围保护)': 0x8612, '0x8481': 0x8481, '0x7180': 0x7180,
         '0x8611': 0x8611, '0x8613': 0x8613, '0xFF01': 0xFF01}

for path, base, ver in SAMPLES:
    d = io.open(path, 'rb').read()
    print('=' * 78)
    print('%s  %s  %d bytes  (load base 0x%08X)' % (ver, path.split('\\')[-1], len(d), base))
    print('=' * 78)
    for name, code in CODES.items():
        hits16 = []
        pat = struct.pack('<H', code)
        i = d.find(pat)
        while i >= 0 and len(hits16) < 32:
            hits16.append(i)
            i = d.find(pat, i + 1)
        hits32 = []
        pat32 = struct.pack('<I', code)
        i = d.find(pat32)
        while i >= 0 and len(hits32) < 32:
            hits32.append(i)
            i = d.find(pat32, i + 1)
        if not hits16 and not hits32:
            continue
        print('  %-26s  16bit命中 %-3d  32bit命中 %-3d' % (name, len(hits16), len(hits32)))
        # 看 16bit 命中里有没有"成组出现"（表）的
        if len(hits16) >= 3:
            gaps = [hits16[k + 1] - hits16[k] for k in range(min(8, len(hits16) - 1))]
            print('      前几处偏移: %s' % ' '.join('0x%06X' % h for h in hits16[:8]))
            print('      相邻间隔  : %s' % gaps)
    print('')
