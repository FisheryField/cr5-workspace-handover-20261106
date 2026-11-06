#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描 .rdk 解压字节流中全部 UTF-16LE 文本段，枚举站点对象名。"""
import struct, zlib, re, io

PATH = r"D:\mydata\working things\dobot_arm\RoboDK files 2\2026-9-7.rdk"
raw = open(PATH, "rb").read()
data = zlib.decompress(raw[4:])

def valid_unit(u):
    # ASCII 可打印
    if u < 0x80 and u >= 0x20:
        return True
    # CJK 基本
    if 0x4E00 <= u <= 0x9FFF:
        return True
    # CJK 标点/全角
    if 0x3000 <= u <= 0x303F or 0xFF00 <= u <= 0xFFEF:
        return True
    if u in (0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x00B7):
        return True
    return False

runs = []
i = 0
n = len(data)
while i + 2 <= n:
    # 尝试在此处开始一个 run（对齐偶/奇都扫）
    j = i
    units = []
    while j + 2 <= n:
        (u,) = struct.unpack("<H", data[j:j + 2])
        if valid_unit(u):
            units.append(u)
            j += 2
        else:
            break
    if len(units) >= 3 and any(0x4E00 <= u <= 0x9FFF for u in units):
        s = "".join(chr(u) for u in units)
        runs.append((i, s))
        i = j
    else:
        i += 1

# 去重输出
seen = {}
for pos, s in runs:
    seen.setdefault(s, []).append(pos)
print("UTF-16LE 含中文文本段 unique:", len(seen))
for s, poss in sorted(seen.items(), key=lambda kv: kv[1][0]):
    print("  at %8d (x%d): %s" % (poss[0], len(poss), s[:70]))
