# -*- coding: utf-8 -*-
"""反汇编 libdataSvr.so 的关键函数，并解析 PC 相对字面量（找出字符串/全局引用）。"""
import struct, re, pathlib, sys
import capstone

P = pathlib.Path(r"D:\mydata\workspace\libdataSvr.so.bin")
d = P.read_bytes()
is64 = d[4] == 2
e_shoff, = struct.unpack_from("<I", d, 32)
e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", d, 46)

def sh(i):
    o = e_shoff + i*e_shentsize
    n,t,f,a,off,sz,lk,inf,al,ent = struct.unpack_from("<IIIIIIIIII", d, o)
    return dict(name=n,typ=t,addr=a,offset=off,size=sz,link=lk,entsize=ent)
secs = [sh(i) for i in range(e_shnum)]
shstr = secs[e_shstrndx]
def sname(n):
    e = d.index(b"\x00", shstr["offset"]+n)
    return d[shstr["offset"]+n:e].decode("ascii","replace")
for s in secs: s["sname"] = sname(s["name"])

syms = {}
for st in secs:
    if st["typ"] not in (2,11): continue
    strtab = secs[st["link"]]
    n = st["size"]//st["entsize"] if st["entsize"] else 0
    for i in range(n):
        o = st["offset"]+i*st["entsize"]
        nm,val,size,info,other,shndx = struct.unpack_from("<IIIBBH", d, o)
        e = d.index(b"\x00", strtab["offset"]+nm)
        name = d[strtab["offset"]+nm:e].decode("ascii","replace")
        if name and (info & 0xF) == 2:
            syms.setdefault(name, (val, size))

def sec_of(addr):
    for s in secs:
        if s["typ"] == 1 and s["addr"] and s["addr"] <= addr < s["addr"]+s["size"]:
            return s
    return None
def str_at(addr, maxlen=80):
    s = sec_of(addr)
    if not s: return None
    o = s["offset"] + (addr - s["addr"])
    if o < 0 or o >= len(d): return None
    e = d.find(b"\x00", o, o+maxlen)
    if e < 0: return None
    raw = d[o:e]
    if len(raw) < 3 or not all(32 <= c < 127 for c in raw): return None
    return raw.decode()

md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.detail = True

def disasm(sym, limit=170):
    if sym not in syms: print(f"!! 符号未找到: {sym}"); return
    addr, size = syms[sym]
    mode = capstone.CS_MODE_THUMB if (addr & 1) else capstone.CS_MODE_ARM
    a0 = addr & ~1
    s = sec_of(a0)
    if not s: print(f"!! 地址 {a0:#x} 不在任何段"); return
    off = s["offset"] + (a0 - s["addr"])
    code = d[off:off+size]
    m = capstone.Cs(capstone.CS_ARCH_ARM, mode); m.detail = True
    print(f"\n===== {sym}  @0x{a0:x}  size={size}  {'THUMB' if mode==capstone.CS_MODE_THUMB else 'ARM'} =====")
    n = 0
    for ins in m.disasm(code, a0):
        note = ""
        # PC 相对字面量
        for op in ins.operands:
            if op.type == capstone.arm.ARM_OP_MEM and op.mem.base == capstone.arm.ARM_REG_PC:
                lit = (ins.address + 4) & ~3
                if mode == capstone.CS_MODE_THUMB:
                    lit = ((ins.address + 4) & ~3) + op.mem.disp
                else:
                    lit = ins.address + 8 + op.mem.disp
                # 读取该字面量
                ls = sec_of(lit)
                if ls:
                    lo = ls["offset"] + (lit - ls["addr"])
                    if lo + 4 <= len(d):
                        v = struct.unpack_from("<I", d, lo)[0]
                        st = str_at(v)
                        note += f"   ; [0x{lit:x}] = 0x{v:x}" + (f'  "{st}"' if st else "")
            if op.type == capstone.arm.ARM_OP_IMM and ins.mnemonic in ("bl","blx","b"):
                t = op.imm
                for nm,(va,sz) in syms.items():
                    if (va & ~1) == (t & ~1):
                        note += f"   ; -> {nm[:60]}"; break
        print(f"  {ins.address:08x}  {ins.mnemonic:<8}{ins.op_str}{note}")
        n += 1
        if n >= limit:
            print("  ... (截断)"); break

for s in sys.argv[1:] or ["_ZN14DataSubProcess8caliHomeEP14evhttp_requestPv",
                          "_ZN14DataSubProcess16updateEncoderDataEv"]:
    disasm(s)
