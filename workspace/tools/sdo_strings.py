# -*- coding: utf-8 -*-
"""从 libdataSvr.so 里找 SDO 读写用的配置文件名与路径线索。"""
import re, pathlib, collections
P = pathlib.Path(r"D:\mydata\workspace\libdataSvr.so.bin")
d = P.read_bytes()
S = re.findall(rb"[ -~]{4,}", d)
S = [s.decode("ascii", "replace") for s in S]

def show(title, pat, limit=40):
    rx = re.compile(pat, re.I)
    hits = [s for s in S if rx.search(s)]
    seen, out = set(), []
    for s in hits:
        if s not in seen:
            seen.add(s); out.append(s)
    print(f"\n===== {title}  ({len(out)} 条) =====")
    for s in out[:limit]:
        print("   ", s[:130])

show("含 sdo 的字符串", r"sdo")
show("项目内路径（/dobot/userdata 下）", r"/dobot/userdata/[A-Za-z0-9_./-]+")
show("含 param/Param 的路径或文件名", r"[A-Za-z0-9_./-]*param[A-Za-z0-9_./-]*")
show("含 cali/home/encoder/zero 的字符串", r"calihome|homeEncoder|innerEncoder|outEncoder|zero|Zero")
