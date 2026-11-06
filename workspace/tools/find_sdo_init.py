# -*- coding: utf-8 -*-
"""定位 'init sdo index map' 的引用代码与它使用的静态表。"""
import struct, re, pathlib, bisect

P = pathlib.Path(r"D:\mydata\workspace\libdataSvr.so.bin")
data = P.read_bytes()
is64 = data[4] == 2
e_shoff, = struct.unpack_from("<I", data, 32)
e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)

def sh(i):
    o = e_shoff + i * e_shentsize
    n, t, f, a, off, sz, lk, inf, al, ent = struct.unpack_from("<IIIIIIIIII", data, o)
    return dict(name=n, typ=t, addr=a, offset=off, size=sz, link=lk, entsize=ent)

secs = [sh(i) for i in range(e_shnum)]
shstr = secs[e_shstrndx]
def sname(n):
    end = data.index(b"\x00", shstr["offset"] + n)
    return data[shstr["offset"] + n:end].decode("ascii", "replace")
for s in secs: s["sname"] = sname(s["name"])

# --- 符号表：地址 -> 名称 ---
syms = []
for st in secs:
    if st["typ"] not in (2, 11): continue
    strtab = secs[st["link"]]
    n = st["size"] // st["entsize"] if st["entsize"] else 0
    for i in range(n):
        o = st["offset"] + i * st["entsize"]
        nm, val, size, info, other, shndx = struct.unpack_from("<IIIBBH", data, o)
        end = data.index(b"\x00", strtab["offset"] + nm)
        name = data[strtab["offset"] + nm:end].decode("ascii", "replace")
        if name and val and (info & 0xF) == 2:   # STT_FUNC
            syms.append((val, size, name))
syms.sort()
addrs = [s[0] for s in syms]
def sym_at(a):
    i = bisect.bisect_right(addrs, a) - 1
    if i >= 0:
        v, sz, nm = syms[i]
        if v <= a < v + max(sz, 1) or (a - v) < 0x400:
            return f"{nm} (+{a - v:#x})"
    return "?"

# --- 找字符串地址 ---
def str_addr(s):
    out = []
    for sec in secs:
        if sec["typ"] != 1 or not sec["addr"]: continue   # PROGBITS
        seg = data[sec["offset"]:sec["offset"] + sec["size"]]
        idx = seg.find(s)
        while idx != -1:
            out.append(sec["addr"] + idx)
            idx = seg.find(s, idx + 1)
    return out

for target in [b"init sdo index map", b"start read sdo from codesys", b"start write sdo tp codesys",
               b"sdo write,slave={},index={},subIndex={},value={}."]:
    addrs_found = str_addr(target)
    print(f"\n### 字符串 {target.decode()!r} 地址: {[hex(a) for a in addrs_found]}")
    for sa in addrs_found:
        # 在 .text 中找引用该地址的字面量（ARM 字面量池）
        pat = struct.pack("<I", sa)
        for sec in secs:
            if sec["typ"] != 1 or not (sec["addr"] and sec["size"]): continue
            seg = data[sec["offset"]:sec["offset"] + sec["size"]]
            i = seg.find(pat)
            while i != -1:
                va = sec["addr"] + i
                print(f"    引用 @ {va:#010x}  所在函数: {sym_at(va)}")
                i = seg.find(pat, i + 1)
