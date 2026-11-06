
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
# --- 动态符号
ds, dstr = S['.dynsym'], S['.dynstr']
def dynsym_name(idx):
    o=ds["offset"]+idx*16
    nm,val,size,info,other,shndx=struct.unpack_from("<IIIBBH", d, o)
    e=d.index(b"\x00", dstr["offset"]+nm)
    return d[dstr["offset"]+nm:e].decode("ascii","replace")
rp=S['.rel.plt']; n=rp["size"]//8
slot2sym={}
order=[]
for i in range(n):
    r_off, r_info = struct.unpack_from("<II", d, rp["offset"]+i*8)
    nm = dynsym_name(r_info>>8)
    slot2sym[r_off]=nm; order.append(r_off)
def ror(v,r): return ((v>>r)|(v<<(32-r)))&0xffffffff
def imm(w):
    v=w&0xfff; return ror(v&0xff, 2*((v>>8)&0xf))
def stub_slot(a):
    h1,h2,h3 = struct.unpack_from("<III", d, a)
    # 允许 add ip,pc,#0 (有些桩 h1 = e28fc600)
    if (h1 & 0xfffff000)!=0xe28fc000: return None
    if (h2 & 0xfffff000)!=0xe28cc000: return None
    if (h3 & 0xfffff000)!=0xe5bcf000: return None
    return ((a+8)&~3) + imm(h1) + imm(h2) + (h3&0xfff)
pl=S['.plt']
lo,hi = pl["addr"], pl["addr"]+pl["size"]
# 在 .plt 内 2 字节对齐扫描
found={}
seq=[]
for a in range(lo, hi-12, 2):
    s = stub_slot(a)
    if s is None: continue
    if s in slot2sym:
        found[a]=slot2sym[s]
        if s not in [x[1] for x in seq]: seq.append((a,s))
print("扫到桩 %d 个；.rel.plt 条目 %d 条；去重槽位 %d" % (len(found), n, len(seq)))
missing=[s for s in order if s not in [x[1] for x in seq]]
print("未被任何桩命中的 GOT 槽: %d" % len(missing))
print()
print("=== 桩地址 -> 符号（按地址排序，前 25）===")
for a in sorted(found)[:25]:
    print("   0x%06x  %s" % (a, found[a]))
print()
# 分步长统计
ads=sorted(found)
from collections import Counter
print("相邻桩间距分布:", Counter(ads[i+1]-ads[i] for i in range(len(ads)-1)).most_common(6))
json.dump({hex(k):v for k,v in found.items()}, open(r'D:\mydata\workspace\tools\plt_map.json','w'))
print("\n已写 tools/plt_map.json  (%d 条)" % len(found))
