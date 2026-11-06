
import struct
P = r"D:\mydata\workspace\libdataSvr.so.bin"
d=open(P,'rb').read()
e_shoff,=struct.unpack_from("<I",d,32); e_shentsize,e_shnum,e_shstrndx=struct.unpack_from("<HHH",d,46)
secs=[]
for i in range(e_shnum):
    o=e_shoff+i*e_shentsize
    n,t,f,a,off,sz,lk,inf,al,ent=struct.unpack_from("<IIIIIIIIII",d,o)
    secs.append(dict(typ=t,addr=a,off=off,size=sz))
for x in secs: x["sname"]=None
def a2o(a):
    for x in secs:
        if x["typ"]!=8 and x["addr"]<=a<x["addr"]+x["size"]: return x["off"]+(a-x["addr"])
    return None
def show(tag, a):
    o=a2o(a)
    print("  %-24s VA=0x%08x  文件偏移=%s" % (tag, a, ("0x%x"%o) if o is not None else "None"))
    if o is None: return
    print("      hex : %s" % d[o:o+48].hex(' '))
    print("      ascii: %r" % d[o:o+48])
# 各处 (ldr地址, pc偏移, add地址)
sites=[("成员名 ldr@11a322",0x11a322,0x244,0x11a326),
       ("L1 ldr@11a36e",0x11a36e,0x7f,0x11a372),
       ("路径 ldr@11a3aa",0x11a3aa,0x75,0x11a3ae),
       ("L4 ldr@11a3b6",0x11a3b6,0x73,0x11a3c0)]
for tag,la,do,aa in sites:
    la_lit=((la+4)&~3)+do
    v,=struct.unpack_from("<I",d,la_lit)
    pc=(aa+4)&~3
    print("%s : 字面量@0x%x v=0x%08x  add@0x%x pc=0x%x  目标=0x%08x" % (tag,la_lit,v,aa,pc,(v+pc)&0xffffffff))
    show("  ->目标", (v+pc)&0xffffffff)
