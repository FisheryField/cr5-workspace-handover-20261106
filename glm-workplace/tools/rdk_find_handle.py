#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在 .rdk 解压流中搜“门把手/把手/handle”条目（UTF-8 与 UTF-16LE 两种编码）。"""
import io, re

text = io.open(r"D:\mydata\glm-workplace\data\scripts_ref\rdk_extract.txt", encoding="utf-8", errors="replace").read()

def show(title, hits, enc):
    print("== %s（%s，共 %d 处）==" % (title, enc, len(hits)))
    for pos in hits[:20]:
        lo = max(0, pos - 500)
        ctx = text[lo:pos + 500]
        if enc == "UTF-16LE":
            # 还原成可读
            ctx = ctx.replace("\x00", "")
        ctx = re.sub(r"[\x00-\x08\x0b-\x1f\x7f-\xff]", "·", ctx)
        print("---- at %d ----" % pos)
        print(ctx)
        print()

# UTF-8 直接编码
for kw in ["门把手", "把手", "handle", "Handle"]:
    hits = [m.start() for m in re.finditer(re.escape(kw), text)]
    if hits:
        show(kw, hits, "UTF-8")

# UTF-16LE：每个字符后跟 \x00
for kw in ["门把手", "把手"]:
    pat = "".join(re.escape(c) + r"\x00" for c in kw)
    hits = [m.start() for m in re.finditer(pat, text)]
    if hits:
        show(kw, hits, "UTF-16LE")
