
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
    if (info&0xf)==2 and val: sym.setdefault(sec["addr"]+(val&~1), n2)
print("=== 0x1a7e00..0x1a8400 内的函数符号 ===")
for k in sorted(sym):
    if 0x1a7e00 <= k < 0x1a8400:
        print("   @0x%06x  %s" % (k, sym[k]))
T = S['.text']; lo,hi = T["addr"], T["addr"]+T["size"]
def movw_hits(imm):
    imm4 = (imm>>8)&0xf; i=(imm>>11)&1; imm3=(imm>>3)&0x7; imm8=imm&0xff
    hw1 = 0xF240 | (i<<10) | imm4
    res=[]
    b1=struct.pack("<H",hw1)
    p=lo
    while True:
        q=d.find(b1, a2o(p) if p==lo else a2o(p), a2o(hi))
        if q<0: break
        p = lo + (q - a2o(lo))
        if p+4<=hi:
            hw2,=struct.unpack_from("<H", d, q+2)
            if ((hw2>>12)&0x7)==imm3 and (hw2&0xff)==imm8:
                res.append((p, (hw2>>8)&0xf))
        p += 2
        if p>=hi: break
    return res
for imm,lbl in ((4613,'readSDO 起始日志 #4613'),(4624,'readSDO 失败日志 #4624'),(4685,'parseAndReqGet 进入 #4685')):
    hs=movw_hits(imm)
    print()
    print("### movw #%d (=0x%x)  %s   命中 %d 处" % (imm, imm, lbl, len(hs)))
    for a,rd in hs[:12]:
        enc=None
        for k in sorted(sym):
            if k<=a and (enc is None or k>enc[0]): enc=(k,sym[k])
        print("   @0x%06x  r%d   所属: %s @0x%x" % (a, rd, enc[1].split('(')[0] if enc else '?', enc[0] if enc else 0))
