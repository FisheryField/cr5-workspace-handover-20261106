#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v3150 里 0x8612 的 32 位常量只有 1 处 —— 反汇编它周边的代码，找判据。"""
import io
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB  # noqa: E402

P = r'D:\mydata\workspace\data\servo_fw_samples\elf\v3150.bin'
BASE = 0x08010000
d = io.open(P, 'rb').read()

for code, name in ((0x8612, '0x8612 位置给定超限保护'), (0x8481, '0x8481 速度偏差过大'),
                   (0x7180, '0x7180 电机过载')):
    hits = []
    pat = struct.pack('<I', code)
    i = d.find(pat)
    while i >= 0:
        hits.append(i)
        i = d.find(pat, i + 1)
    print('=' * 76)
    print('%s   32位常量命中 %d 处: %s' % (name, len(hits), ' '.join('0x%06X' % h for h in hits)))
    print('=' * 76)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    for h in hits[:3]:
        start = max(0, h - 0x60)
        end = min(len(d), h + 0x30)
        print('--- flash 0x%06X (runtime 0x%08X) 附近 ---' % (h, BASE + h))
        for ins in md.disasm(d[start:end], BASE + start):
            mark = '   <<< 常量在此' if ins.address - BASE == h else ''
            print('  %08X  %-8s %s%s' % (ins.address, ins.mnemonic, ins.op_str, mark))
        print('')
