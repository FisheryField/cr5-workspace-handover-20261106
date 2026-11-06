
import struct
P = r"D:\mydata\workspace\libdataSvr.so.bin"
d=open(P,'rb').read()
e_shoff,=struct.unpack_from("<I",d,32); e_shentsize,e_shnum,e_shstrndx=struct.unpack_from("<HHH",d,46)
secs=[]
for i in range(e_shnum):
    o=e_shoff+i*e_shentsize
    n,t,f,a,off,sz,lk,inf,al,ent=struct.unpack_from("<IIIIIIIIII",d,o)
    secs.append(dict(typ=t,addr=a,off=off,size=sz))
def a2o(a):
    for x in secs:
        if x["typ"]!=8 and x["addr"]<=a<x["addr"]+x["size"]: return x["off"]+(a-x["addr"])
    return None
def lit(laddr, d_off):
    o=a2o(((laddr+4)&~3)+d_off)
    v,=struct.unpack_from("<I",d,o); return v
def cs(v):
    o=a2o(v)
    if o is None: return None
    try: e=d.index(b"\x00",o)
    except: return None
    if e-o>160: return None
    b=d[o:e]
    try: t=b.decode('utf-8')
    except: return b.decode('latin-1')
    return t
# (ldr地址, 偏移, add地址 或 None)
sites = [
 ("HasMember/成员名 @0x11a322", 0x11a322, 0x244, 0x11a326),
 ("@0x11a312 的 r1",           0x11a312, 0x250, 0x11a31c),
 ("字面量1 @0x11a36e",          0x11a36e, 0x1fc, 0x11a372),
 ("字面量2 @0x11a37c",          0x11a37c, 0x1f0, 0x11a380),
 ("字面量3 @0x11a39c",          0x11a39c, 0x1dc, 0x11a3a0),
 ("access 路径 @0x11a3a8",      0x11a3a8, 0x1d4, 0x11a3ac),
 ("字面量4 @0x11a3b6",          0x11a3b6, 0x1cc, 0x11a3c0),
 ("log参数 @0x11a3de",          0x11a3de, 0x1a8, 0x11a3f0),
]
for name, la, do, aa in sites:
    v = lit(la, do)
    for pcbase in (((aa+4)&~3), (aa+2)&~3):
        t = cs((v+pcbase)&0xffffffff)
        if t: print("  %-28s -> \"%s\"" % (name, t[:120])); break
    else:
        print("  %-28s -> 0x%x (未能解成字符串)" % (name, v))
print()
print("=== 该函数内其它 pc 相对字面量 ===")
import struct as _s
for a in range(0x11a1ac, 0x11a1ac+1016, 2):
    w,= _s.unpack_from("<H", d, a2o(a))
    if (w & 0xF800)==0x4800:
        imm8=w&0xFF; la=((a+4)&~3)+imm8*4; o=a2o(la)
        if o is None: continue
        v,=_s.unpack_from("<I", d, o)
        t=cs(v)
        if t and len(t)>1: print("   0x%06x ldr->0x%x 直接是字符串: \"%s\"" % (a,v,t[:100]))
