#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在当前版 2026-9-7.rdk 解压字节流中定位 门把手_bs1（多编码搜索）。"""
import struct, zlib, re

PATH = r"D:\mydata\working things\dobot_arm\RoboDK files 2\2026-9-7.rdk"
raw = open(PATH, "rb").read()
print("file bytes:", len(raw))
data = zlib.decompress(raw[4:])
print("decompressed:", len(data))

targets = {
    "门把手_bs1": [lambda s: s.encode("utf-16-le"), lambda s: s.encode("utf-8"), lambda s: s.encode("gbk")],
    "门把手": [lambda s: s.encode("utf-16-le"), lambda s: s.encode("utf-8"), lambda s: s.encode("gbk")],
    "把手": [lambda s: s.encode("utf-16-le"), lambda s: s.encode("utf-8")],
    "_bs1": [lambda s: s.encode("ascii"), lambda s: s.encode("utf-16-le")],
    "bs1": [lambda s: s.encode("ascii"), lambda s: s.encode("utf-16-le")],
}

for name, encs in targets.items():
    for enc in encs:
        try:
            pat = enc(name)
        except Exception:
            continue
        hits = [m.start() for m in re.finditer(re.escape(pat), data)]
        if hits:
            print("[%s x%d @ %s]" % (name, len(hits), enc.__name__ + ":" + str(pat[:12])))
            for h in hits[:8]:
                # 打印前后文（UTF-16 尝试解码）
                ctx = data[max(0, h - 120):h + 200]
                t = ctx.decode("utf-16-le", "ignore")
                t2 = ctx.decode("utf-8", "ignore")
                t = re.sub(r"[^\u3000-\u9fffA-Za-z0-9_.,:\- ]", "·", t)
                t2 = re.sub(r"[^\u3000-\u9fffA-Za-z0-9_.,:\- ]", "·", t2)
                print("   @%d U16: %s" % (h, t[:120]))
                print("        U8 : %s" % t2[:120])
