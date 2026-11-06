# -*- coding: utf-8 -*-
"""列出 libdataSvr.so 中与 servo / param 相关的 HTTP 路由字符串。"""
import re, pathlib
d = pathlib.Path(r"D:\mydata\workspace\libdataSvr.so.bin").read_bytes()
S = [s.decode("ascii", "replace") for s in re.findall(rb"[ -~]{3,}", d)]

def uniq(seq):
    seen, out = set(), []
    for s in seq:
        if s not in seen:
            seen.add(s); out.append(s)
    return out

print("===== 以 / 开头的路由（含 servo/param/motor/axis/cali）=====")
routes = [s for s in S if s.startswith("/") and re.search(r"servo|param|motor|axis|cali|home|zero", s, re.I)]
for s in uniq(routes)[:60]:
    print("   ", s[:120])

print("\n===== 全部 / 开头的路由（抽样 80 条，看命名规律）=====")
allr = [s for s in S if re.match(r"^/[a-zA-Z][A-Za-z0-9_/\-]{2,60}$", s)]
for s in uniq(allr)[:80]:
    print("   ", s[:100])

print("\n===== 字符串中直接出现的 slave/index/subIndex 相关 =====")
for s in uniq([s for s in S if re.search(r"slave=|index=|subIndex=|index map|SDOInfo|servoParam", s, re.I)])[:40]:
    print("   ", s[:130])
