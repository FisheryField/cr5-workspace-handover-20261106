
import struct, json
from capstone import *
P = r"D:\mydata\workspace\libdataSvr.so.bin"
d = open(P,'rb').read()
e_shoff, = struct.unpack_from("<I", d, 32)
e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", d, 46)
def sh(i):
    o=e_shoff+i*e_shentsize
    n,t,f,a,off,sz,lk,inf,al,ent = struct.unpack_from("<IIIIIIIIII", d, o)
    return dict(idx=i,name=n,typ=t,addr=a,offset=off,size=sz,link=lk,info=inf,entsize=ent)
secs=[sh(i) for i in range(e_shnum)]
shstr=secs[e_shstrndx]
def sname(n):
    e=d.index(b"\x00", shstr["offset"]+n); return d[shstr["offset"]+n:e].decode("ascii","replace")
for s in secs: s["sname"]=sname(s["name"])
S={}
for s in secs: S.setdefault(s["sname"], s)
def a2o(a):
    for s in secs:
        if s["typ"]!=8 and s["addr"]<=a<s["addr"]+s["size"]:
            return s["offset"]+(a-s["addr"])
    return None
sym={}
st, sr = S['.symtab'], S['.strtab']
for i in range(st["size"]//16):
    o=st["offset"]+i*16
    nm,val,size,info,other,shndx=struct.unpack_from("<IIIBBH", d, o)
    if nm==0 or shndx==0 or shndx>=len(secs): continue
    sec=secs[shndx]
    if sec["typ"]==8: continue
    e=d.index(b"\x00", sr["offset"]+nm)
    n2=d[sr["offset"]+nm:e].decode("ascii","replace")
    if (info&0xf)==2 and val: sym[sec["addr"]+val]=n2
md=Cs(CS_ARCH_ARM, CS_MODE_THUMB)
# 找引用某地址的指令
textlo, texthi = None, None
for s in secs:
    if s["sname"]=='.text': textlo,texthi = s["addr"], s["addr"]+s["size"]
print(".text = 0x%x .. 0x%x" % (textlo,texthi))
def enclosing(a):
    best=None
    for k,v in sym.items():
        if (k&~1) <= a and (best is None or (k&~1) > best[0]):
            best=((k&~1), v)
    return best
def findrefs(target, maxhits=8):
    hits=[]
    lo,hi = textlo, texthi
    # 字面量池几乎都在 .text 内；直接扫 .text 的 4 字节，找等于 target / target|1 的字面量
    for p in range(lo, hi-4, 2):
        v,=struct.unpack_from("<I", d, a2o(p))
        if v!=target and v!=(target|1): continue
        # 回头找 ldr rX,[pc,#imm] 使其字面量地址 == p
        for q in range(p-4, max(p-0x400,lo), -2):
            w,=struct.unpack_from("<H", d, a2o(q))
            if (w & 0xF800) != 0x4800: continue      # LDR Rt,[PC,#imm8]
            imm8 = w & 0xFF
            la = ((q+4)&~3) + imm8*4
            if la==p:
                hits.append((q,p)); break
        if len(hits)>=maxhits: break
    return hits
for name,addr in (("sdo read(fmt #4613)",0x20b780),
                  ("sdo read fail(#4624)",0x20b738),
                  ("start read sdo(#4716)",0x20b8a8),
                  ("the key is error(#4710)",0x20b83c),
                  ("parseAndReqGet(#4685)",0x20b7b4)):
    # 确认字符串实际起始
    o=a2o(addr)
    e=d.index(b"\x00",o)
    print()
    print("### %s  @0x%x  \"%s\"" % (name, addr, d[o:e].decode('latin-1')))
    hs=findrefs(addr)
    for q,p in hs:
        enc=enclosing(q)
        print("   ref @0x%06x (lit@0x%06x)   所属: %s @0x%x" % (q,p, (enc[1].split('(')[0] if enc else '?'), (enc[0] if enc else 0)))
    if not hs: print("   (无引用)")
