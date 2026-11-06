#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在 3.1.5.hex（完整 1 MiB flash 镜像）里定位并提取 XML 配置区。"""
import hashlib
import os
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HEX = r'D:\mydata\working things\机械臂控制柜数据\3.1.5.hex'
XML = r'D:\mydata\workspace\data\official\pkg\CR_Servo_ST_XML_V3.0.0.bin'
OUT = r'D:\mydata\workspace\servo_fw\CR_Servo_ST_XML_V3.0.0_FROM_3150_HEX.bin'

img = bytearray(b'\xff' * 0x100000)
seen = bytearray(0x100000)
base = 0
with open(HEX, 'r', errors='replace') as f:
    for line in f:
        line = line.strip()
        if not line.startswith(':'):
            continue
        raw = bytes.fromhex(line[1:])
        n, addr, typ = raw[0], (raw[1] << 8) | raw[2], raw[3]
        data = raw[4:4 + n]
        if typ == 0x00:
            off = (base + addr) - 0x08000000
            img[off:off + n] = data
        elif typ == 0x01:
            break
        elif typ == 0x02:
            base = int.from_bytes(data, 'big') << 4
        elif typ == 0x04:
            base = int.from_bytes(data, 'big') << 16

x = open(XML, 'rb').read()
print('厂商 XML 文件 %d 字节, md5=%s' % (len(x), hashlib.md5(x).hexdigest()))
print('  头 16 字节: %s' % x[:16].hex(' '))
print('')

# 1) 整份 XML 是否原样出现在镜像里
pos = img.find(bytes(x))
print('整份 XML 在镜像中的位置: %s' % ('0x%08X' % (0x08000000 + pos) if pos >= 0 else '未找到 ✗'))

# 2) 用 XML 里的特征串/头找候选
print('')
print('=== 特征串搜索 ===')
for name, pat in (('头 89 0e 80 44', bytes.fromhex('890e8044')),
                  ('"Dobot DS121"', b'Dobot DS121'),
                  ('"Servo Drives"', b'Servo Drives'),
                  ('"position actual value"', b'position actual value'),
                  ('"receive pdo1"', b'receive pdo1')):
    hits = []
    i = img.find(pat)
    while i >= 0 and len(hits) < 8:
        hits.append(i)
        i = img.find(pat, i + 1)
    print('  %-24s %d 处  %s' % (name, len(hits), ' '.join('0x%08X' % (0x08000000 + h) for h in hits)))

# 3) 若找到 XML 特征，dump 周边区域，判断它的边界与是否带 FoE 头
if pos >= 0:
    start = pos
    # 往前看 0x40 字节，往后看 0x40
    print('')
    print('=== XML 前后各 0x40 字节（看是否有 FoE 头/边界标记）===')
    lo = max(0, start - 0x40)
    hi = min(len(img), start + len(x) + 0x40)
    for i in range(lo, hi, 16):
        row = img[i:i + 16]
        tag = ''
        if i <= start < i + 16:
            tag = '  <== XML 开始'
        if start + len(x) - 1 < i + 16 <= start + len(x) + 16:
            tag = '  <== XML 结束'
        txt = ''.join(chr(b) if 32 <= b < 127 else '.' for b in row)
        print('  %08X  %-47s  %s%s' % (0x08000000 + i, row.hex(' '), txt, tag))

    # 4) 提取并保存
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'wb').write(bytes(x))
    print('')
    print('已按镜像中的同一份内容保存: %s' % OUT)
    print('  （整份 XML 与厂商 V3.0.0 文件逐字节一致 ⇒ 3.1.5.0 机器上用的就是 V3.0.0 XML ✓）')
else:
    # 未找到整份 —— 找最接近的片段长度，判断是否被截断/有偏移
    print('')
    print('=== 未找到完整 XML，改找最长匹配前缀 ===')
    best = 0
    for L in (2048, 1984, 1920, 1792, 1536, 1024, 512, 256, 128, 64):
        if img.find(bytes(x[:L])) >= 0:
            best = L
            break
    print('  最长可匹配前缀 = %d 字节' % best)
    if best:
        p = img.find(bytes(x[:best]))
        print('  位置 0x%08X' % (0x08000000 + p))
        print('  XML 第 %d 字节处开始不一致 ⇒ 可能是"镜像里的 XML 是另一版本"' % best)
        print('  镜像中该处往后的 64 字节:')
        print('   ', img[p + best:p + best + 64].hex(' '))
        print('  厂商文件同处往后的 64 字节:')
        print('   ', x[best:best + 64].hex(' '))
