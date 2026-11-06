
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
def cs(v):
    o=a2o(v)
    if o is None: return None
    try: e=d.index(b"\x00",o)
    except: return None
    if e-o>160: return None
    b=d[o:e]
    try: t=b.decode('utf-8')
    except: return b.decode('latin-1')
    return t if all(31<c<127 or c in (9,10,13) for c in b) else None
print("=== modifyServoParams 内所有 ldr rX,[pc,#imm] 的字面量池 ===")
for a in range(0x11a1ac, 0x11a1ac+1016, 2):
    w,=struct.unpack_from("<H", d, a2o(a))
    if (w & 0xF800)==0x4800:
        rd=(w>>8)&7; imm8=w&0xFF; la=((a+4)&~3)+imm8*4
        o=a2o(la)
        if o is None: continue
        v,=struct.unpack_from("<I", d, o)
        # 该 ldr 之后 6 条指令内是否有 add rX,pc
        tgt=None
        for b in range(a+2, a+14, 2):
            w2,=struct.unpack_from("<H", d, a2o(b))
            if (w2 & 0xFF87)==0x4478 and ((w2>>3)&7)==rd:   # add rX, pc
                tgt=(v + ((b+4)&~3)) & 0xffffffff
                break
        s = cs(v) or (cs(tgt) if tgt else None)
        mark = ""
        if s: mark = ' "%s"' % s[:90]
        print("  0x%06x ldr r%d,[pc,#0x%x] lit@0x%06x v=0x%08x%s" % (a,rd,imm8,la,v,mark))
