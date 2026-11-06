
import struct, json
P = r"D:\mydata\workspace\libdataSvr.so.bin"
d = open(P,'rb').read()
e_shoff, = struct.unpack_from("<I", d, 32)
e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", d, 46)
def sh(i):
    o=e_shoff+i*e_shentsize
    n,t,f,a,off,sz,lk,inf,al,ent = struct.unpack_from("<IIIIIIIIII", d, o)
    return dict(idx=i,name=n,typ=t,flags=f,addr=a,offset=off,size=sz,link=lk,info=inf,entsize=ent)
secs=[sh(i) for i in range(e_shnum)]
shstr=secs[e_shstrndx]
def sname(n):
    e=d.index(b"\x00", shstr["offset"]+n); return d[shstr["offset"]+n:e].decode("ascii","replace")
for s in secs: s["sname"]=sname(s["name"])
S={s["sname"]:s for s in secs}
def a2o(addr):
    for s in secs:
        if s["typ"]!=8 and s["addr"]<=addr<s["addr"]+s["size"]:
            return s["offset"]+(addr-s["addr"])
    return None
# reloc r_offsets
rp=S['.rel.plt']; n=rp["size"]//8
roffs=[struct.unpack_from("<II", d, rp["offset"]+i*8)[0] for i in range(n)]
pl=S['.plt']
print("=== 校验 PLT 桩 -> GOT 槽 ===")
ok=bad=0
for i in range(0,10):
    a = pl["addr"]+20+i*12
    o = a2o(a)
    b = d[o:o+12]
    h1,h2,h3 = struct.unpack_from("<III", b, 0)
    # add ip,pc,#imm  / add ip,ip,#imm / ldr pc,[ip,#imm]!
    okc = ((h1>>24)==0xe2) and ((h1>>16)&0xf)==0xf and ((h1>>12)&0xf)==0xc
    # 计算 GOT 槽
    pc1 = (a+4) & ~3
    imm1 = ((h1&0xff)<<24) | (((h1>>12)&0xf)<<8)   # arm rotate form
    v1 = pc1 + imm1
    pc2 = (a+4) & ~3
    imm2 = h2 & 0xfff
    v2 = v1 + imm2
    imm3 = h3 & 0xfff
    slot = v2 + imm3
    m = "OK " if slot==roffs[i] else "BAD"
    if slot==roffs[i]: ok+=1
    else: bad+=1
    print("  [%s] plt 0x%06x bytes=%s  computed_slot=0x%08x  reloc.r_offset=0x%08x" % (
        m, a, b.hex(), slot, roffs[i]))
print("ok=%d bad=%d" % (ok,bad))
# GOT 基址
gr=S.get('.got')
print("  .got addr=0x%x size=%d -> 0x%x..0x%x" % (gr["addr"],gr["size"],gr["addr"],gr["addr"]+gr["size"]))
