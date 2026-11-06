# -*- coding: utf-8 -*-
"""提取指定函数的调用目标（解析成符号名），用于判断它是否触及 SDO/文件写入。"""
import struct, re, pathlib, sys
import capstone

P = pathlib.Path(r"D:\mydata\workspace\libdataSvr.so.bin")
d = P.read_bytes()
e_shoff, = struct.unpack_from("<I", d, 32)
e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", d, 46)
def sh(i):
    o = e_shoff+i*e_shentsize
    n,t,f,a,off,sz,lk,inf,al,ent = struct.unpack_from("<IIIIIIIIII", d, o)
    return dict(name=n,typ=t,addr=a,offset=off,size=sz,link=lk,entsize=ent)
secs=[sh(i) for i in range(e_shnum)]
shstr=secs[e_shstrndx]
def sname(n):
    e=d.index(b"\x00", shstr["offset"]+n); return d[shstr["offset"]+n:e].decode("ascii","replace")
for s in secs: s["sname"]=sname(s["name"])
funcs=[]; syms={}
for st in secs:
    if st["typ"] not in (2,11): continue
    strtab=secs[st["link"]]
    n=st["size"]//st["entsize"] if st["entsize"] else 0
    for i in range(n):
        o=st["offset"]+i*st["entsize"]
        nm,val,size,info,other,shndx=struct.unpack_from("<IIIBBH", d, o)
        e=d.index(b"\x00", strtab["offset"]+nm)
        name=d[strtab["offset"]+nm:e].decode("ascii","replace")
        if name and (info & 0xF)==2:
            if size: funcs.append((val & ~1, size, name))
            syms[name]=(val & ~1, size)
byname={nm:(a,sz) for a,sz,nm in funcs}
def sec_of(addr):
    for s in secs:
        if s["typ"]==1 and s["addr"] and s["addr"]<=addr<s["addr"]+s["size"]: return s
    return None
def str_at(addr, mx=120):
    s=sec_of(addr)
    if not s: return None
    o=s["offset"]+(addr-s["addr"])
    e=d.find(b"\x00", o, o+mx)
    if e<0: return None
    raw=d[o:e]
    if len(raw)<4 or not all(32<=c<127 for c in raw): return None
    return raw.decode()

def calls(sym):
    if sym not in byname: print(f"!! {sym} 未找到"); return
    a0,size = byname[sym]
    s=sec_of(a0)
    off=s["offset"]+(a0-s["addr"])
    code=d[off:off+size]
    m=capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB); m.detail=True
    print(f"\n===== {sym}  @0x{a0:x} size={size} =====")
    seen=set()
    for ins in m.disasm(code, a0):
        if ins.mnemonic in ("bl","blx","b","bx") and ins.operands and ins.operands[0].type==capstone.arm.ARM_OP_IMM:
            t=ins.operands[0].imm
            nm=None
            for (fa,fs,fn) in funcs:
                if fa==(t & ~1): nm=fn; break
            key=(t,nm)
            if key in seen: continue
            seen.add(key)
            print(f"  {ins.address:08x}  -> 0x{t:x}  {nm if nm else '(未命名/外部)'}")
        # 字符串引用
        for op in ins.operands:
            if op.type==capstone.arm.ARM_OP_MEM and op.mem.base==capstone.arm.ARM_REG_PC:
                lit=((ins.address+4)&~3)+op.mem.disp
                ls=sec_of(lit)
                if ls:
                    lo=ls["offset"]+(lit-ls["addr"])
                    if lo+4<=len(d):
                        v=struct.unpack_from("<I", d, lo)[0]
                        st=str_at(v)
                        if st: print(f"  {ins.address:08x}  [lit 0x{lit:x}] = 0x{v:x}  \"{st[:70]}\"")

for s in sys.argv[1:]:
    calls(s)
