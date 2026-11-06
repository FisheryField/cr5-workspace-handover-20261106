# -*- coding: utf-8 -*-
import struct, re, pathlib
P = pathlib.Path(r"D:\mydata\workspace\libdataSvr.so.bin")
d = P.read_bytes()
e_shoff, = struct.unpack_from("<I", d, 32)
e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", d, 46)
def sh(i):
    o = e_shoff+i*e_shentsize
    n,t,f,a,off,sz,lk,inf,al,ent = struct.unpack_from("<IIIIIIIIII", d, o)
    return dict(name=n,typ=t,addr=a,offset=off,size=sz,link=lk,entsize=ent)
secs = [sh(i) for i in range(e_shnum)]
shstr = secs[e_shstrndx]
def sname(n):
    e = d.index(b"\x00", shstr["offset"]+n); return d[shstr["offset"]+n:e].decode("ascii","replace")
for s in secs: s["sname"] = sname(s["name"])
funcs = []
for st in secs:
    if st["typ"] not in (2,11): continue
    strtab = secs[st["link"]]
    n = st["size"]//st["entsize"] if st["entsize"] else 0
    for i in range(n):
        o = st["offset"]+i*st["entsize"]
        nm,val,size,info,other,shndx = struct.unpack_from("<IIIBBH", d, o)
        e = d.index(b"\x00", strtab["offset"]+nm)
        name = d[strtab["offset"]+nm:e].decode("ascii","replace")
        if name and (info & 0xF) == 2 and size:
            funcs.append((val & ~1, size, name))
funcs.sort()
import sys
pat = sys.argv[1] if len(sys.argv) > 1 else "ncoder"
rx = re.compile(pat, re.I)
seen = set()
for a, sz, nm in funcs:
    if rx.search(nm) and nm not in seen:
        seen.add(nm)
        print(f"  0x{a:08x}  size={sz:<6}  {nm}")
print(f"\n(共 {len(seen)} 个匹配 / 总函数 {len(funcs)})")
