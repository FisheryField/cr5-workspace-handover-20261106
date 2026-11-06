
import struct, json
P = r"D:\mydata\workspace\libdataSvr.so.bin"
d = open(P,'rb').read()
e_shoff, = struct.unpack_from("<I", d, 32)
e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", d, 46)
def sh(i):
    o=e_shoff+i*e_shentsize
    n,t,f,a,off,sz,lk,inf,al,ent = struct.unpack_from("<IIIIIIIIII", d, o)
    return dict(idx=i,name=n,typ=t,addr=a,offset=off,size=sz,link=lk,entsize=ent)
secs=[sh(i) for i in range(e_shnum)]
shstr=secs[e_shstrndx]
def sname(n):
    e=d.index(b"\x00", shstr["offset"]+n); return d[shstr["offset"]+n:e].decode("ascii","replace")
for s in secs: s["sname"]=sname(s["name"])
S={s["sname"]:s for s in secs}
rp=S['.rel.plt']; n=rp["size"]//8
roffs=[struct.unpack_from("<II", d, rp["offset"]+i*8)[0] for i in range(n)]
pl=S['.plt']
def compute(a):
    h1,h2,h3 = struct.unpack_from("<III", d, a)
    if (h1 & 0xfffff000)!=0xe28fc000: return None      # add ip,pc,#imm
    if (h2 & 0xfffff000)!=0xe28cc000: return None      # add ip,ip,#imm
    if (h3 & 0xfffff000)!=0xe5bcf000: return None      # ldr pc,[ip,#imm]!
    def ror(v,r): return ((v>>r)|(v<<(32-r)))&0xffffffff
    def imm(w):
        v=w&0xfff; return ror(v&0xff, 2*((v>>8)&0xf))
    pc=(a+8)&~3
    return (pc + imm(h1) + imm(h2) + (h3&0xfff)) & 0xffffffff
for stride in (12,16):
    base=pl["addr"]+20
    ok=0
    for i in range(min(n,3000)):
        a=base+stride*i
        c=compute(a)
        if c is not None and c==roffs[i]: ok+=1
    print("stride=%-3d  前%d项命中 %d" % (stride, min(n,3000), ok))
