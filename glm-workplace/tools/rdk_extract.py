#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解析 RoboDK .rdk（长度前缀 + zlib 块流），搜内部 Python 宏的引用/源码。"""
import struct, zlib, re, sys, io

PATH = r"D:\mydata\working things\dobot_arm\RoboDK files 2\2026-9-7.rdk"

raw = open(PATH, "rb").read()
print("file size:", len(raw))

blocks = []
off = 0
while off < len(raw):
    if off + 4 > len(raw):
        break
    (n,) = struct.unpack(">I", raw[off:off + 4])
    off += 4
    if n == 0:
        blocks.append(b"")
        continue
    try:
        data = zlib.decompress(raw[off:])
    except Exception as e:
        print("zlib fail at off=%d size=%d: %s" % (off, n, e))
        break
    blocks.append(data)
    # 找到该 zlib 流的实际结束位置
    d = zlib.decompressobj()
    d.decompress(raw[off:])
    off += len(raw[off:]) - len(d.unused_data)

print("blocks:", len(blocks), "total decompressed:", sum(len(b) for b in blocks))

# 拼全文（块内多为 XML/文本）
full = b"\n".join(blocks)
text = full.decode("utf-8", "replace")
open(r"D:\mydata\glm-workplace\data\scripts_ref\rdk_extract.txt", "w", encoding="utf-8", errors="replace").write(text)
print("dumped text chars:", len(text))

# 搜 .py 相关引用
for m in re.finditer(r'[^\n"<>]*\.py[^\n"<>]*', text):
    s = m.group(0).strip()
    if s:
        print("PY-REF:", s[:160])
