
import struct, capstone
P = r"D:\mydata\workspace\libdataSvr.so.bin"
d = open(P,'rb').read()
e_shoff, = struct.unpack_from("<I", d, 32)
e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", d, 46)
def sh(i):
    o=e_shoff+i*e_shentsize
    n,t,f,a,off,sz,lk,inf,al,ent = struct.unpack_from("<IIIIIIIIII", d, o)
    return dict(name=n,typ=t,addr=a,offset=off,size=sz,link=lk,entsize=ent)
secs=[sh(i) for i in range(e_shnum)]
shstr=secs[e_shstrndx]
def sname(n):
    e=d.index(b"\x00", shstr["offset"]+n); return d[shstr["offset"]+n:e].decode("ascii","replace")
for s in secs: s["sname"]=sname(s["name"])
syms={}
for st in secs:
    if st["typ"] not in (2,11): continue
    strtab=secs[st["link"]]
    n=st["size"]//st["entsize"] if st["entsize"] else 0
    for i in range(n):
        o=st["offset"]+i*st["entsize"]
        nm,val,size,info,other,shndx=struct.unpack_from("<IIIBBH", d, o)
        e=d.index(b"\x00", strtab["offset"]+nm)
        name=d[strtab["offset"]+nm:e].decode("ascii","replace")
        if name and (info&0xF)==2: syms.setdefault(name,(val,size))
def sec_of(addr):
    for s in secs:
        if s["typ"]==1 and s["addr"] and s["addr"]<=addr<s["addr"]+s["size"]: return s
    return None
def str_at(addr, maxlen=90):
    s=sec_of(addr)
    if not s: return None
    o=s["offset"]+(addr-s["addr"])
    if o<0 or o>=len(d): return None
    e=d.find(b"\x00",o,o+maxlen)
    if e<0: return None
    raw=d[o:e]
    if len(raw)<2 or not all(32<=c<127 for c in raw): return None
    return raw.decode()
def disasm(sym, limit=400):
    if sym not in syms: print("!! 未找到", sym); return
    addr,size=syms[sym]
    mode=capstone.CS_MODE_THUMB if (addr&1) else capstone.CS_MODE_ARM
    a0=addr&~1
    s=sec_of(a0); off=s["offset"]+(a0-s["addr"])
    m=capstone.Cs(capstone.CS_ARCH_ARM, mode); m.detail=True
    print("\n===== %s @0x%x size=%d =====" % (sym[:70], a0, size))
    reglit={}
    n=0
    for ins in m.disasm(d[off:off+size], a0):
        note=""
        op=ins.op_str
        # ldr rX, [pc, #imm] -> 记录字面量
        if ins.mnemonic in ("ldr","ldr.w") and "[pc" in op:
            try:
                imm=ins.operands[1].mem.disp
                lit=((ins.address+4)&~3)+imm
                ls=sec_of(lit)
                if ls:
                    lo=ls["offset"]+(lit-ls["addr"])
                    v=struct.unpack_from("<I", d, lo)[0]
                    reglit[ins.operands[0].reg]=v
                    note="   ; lit=0x%x" % v
            except Exception: pass
        # add rX, pc -> 组合
        if ins.mnemonic=="add" and op.endswith(", pc"):
            try:
                reg=ins.operands[0].reg
                v=reglit.get(reg)
                if v is not None:
                    tgt=((ins.address+4)&~3)+v
                    st=str_at(tgt)
                    note="   ; -> 0x%x" % tgt + ('  "%s"' % st if st else "")
            except Exception: pass
        if note:
            print("  0x%08x  %-10s %-30s%s" % (ins.address, ins.mnemonic, op, note))
        n+=1
        if n>=limit: print("  ...(截断)"); break
disasm("_ZN14DataSubProcess25parseAndReqGetServoParamsEPS_RN9rapidjson15GenericDocumentINS1_4UTF8IcEENS1_19MemoryPoolAllocatorINS1_12CrtAllocatorEEES6_EE", 400)
