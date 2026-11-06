#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""枚举 .rdk 解压流中全部「长度前缀 + UTF-16LE」字符串，列出站点对象名清单。"""
import struct, zlib, re, io

PATH = r"D:\mydata\working things\dobot_arm\RoboDK files 2\2026-9-7.rdk"
raw = open(PATH, "rb").read()
data = zlib.decompress(raw[4:])
print("bytes:", len(data))

# 扫描：<uint32 len> + len 字节 UTF-16LE，要求可解码且字符可打印
def try_string_at(i):
    if i + 4 > len(data):
        return None
    (n,) = struct.unpack("<I", data[i:i + 4])
    if n < 2 or n > 512 or n % 2 != 0 or i + 4 + n > len(data):
        return None
    b = data[i + 4:i + 4 + n]
    try:
        s = b.decode("utf-16-le")
    except Exception:
        return None
    # 全部可打印（含 CJK）
    for ch in s:
        o = ord(ch)
        if o < 0x20 and ch not in "\t":
            return None
        if 0xD800 <= o <= 0xDFFF:
            return None
    return s

results = []
i = 0
while i < len(data) - 6:
    s = try_string_at(i)
    if s and len(s) >= 2 and re.search(r"[\u4e00-\u9fffA-Za-z0-9]", s):
        results.append((i, s))
        i += 4 + len(s.encode("utf-16-le"))
    else:
        i += 1

print("strings found:", len(results))
out = io.open(r"D:\mydata\glm-workplace\data\scripts_ref\rdk_strings.txt", "w", encoding="utf-8")
seen = {}
for pos, s in results:
    seen.setdefault(s, []).append(pos)
for s, poss in sorted(seen.items(), key=lambda kv: -len(kv[1])):
    out.write("%6d x  %s\n" % (len(poss), s[:80]))
out.close()
print("unique:", len(seen))
print("== 前 80 个唯一字符串 ==")
for s, poss in sorted(seen.items(), key=lambda kv: -len(kv[1]))[:80]:
    print("%5d x  %s" % (len(poss), s[:70]))
