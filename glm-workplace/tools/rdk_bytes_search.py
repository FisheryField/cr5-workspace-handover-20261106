#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在 .rdk 解压后的原始字节流上搜对象名（UTF-16LE 为主），列出全部站点对象名。"""
import struct, zlib, re

PATH = r"D:\mydata\working things\dobot_arm\RoboDK files 2\2026-9-7.rdk"
raw = open(PATH, "rb").read()

(n,) = struct.unpack(">I", raw[0:4])
data = zlib.decompress(raw[4:])
print("decompressed bytes:", len(data))

def utf16le(s):
    return s.encode("utf-16-le")

def find_all(pat, label):
    hits = [m.start() for m in re.finditer(re.escape(pat), data)]
    print("[%s] %d hits" % (label, len(hits)))
    return hits

# 多个候选关键词
kws = ["门把手", "把手", "拉手", "门", "handle", "Handle", "door", "Door"]
for kw in kws:
    for enc, encname in [(utf16le(kw), "UTF16"), (kw.encode("utf-8"), "UTF8"), (kw.encode("gbk"), "GBK")]:
        hits = find_all(enc, "%s/%s" % (kw, encname))
        if hits and kw in ("门把手", "把手", "拉手", "handle", "Handle"):
            for h in hits[:6]:
                ctx = data[max(0, h - 200):h + 300]
                try:
                    txt = ctx.decode("utf-16-le", "replace")
                except Exception:
                    txt = repr(ctx)
                txt = re.sub(r"[\x00-\x1f\x7f-\xff]", "·", txt)
                print("   at %d: %s" % (h, txt[:220]))
