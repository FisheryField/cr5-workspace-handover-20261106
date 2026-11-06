
import struct, sys
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
print("=== 关键节 ===")
for s in secs:
    if s["sname"] in ('.plt','.rel.plt','.rela.plt','.got','.got.plt','.dynsym','.dynstr','.data.rel.ro','.rodata'):
        print("  %-14s type=%-3d addr=0x%08x off=0x%08x size=%-8d entsize=%d link=%d" % (
            s["sname"], s["typ"], s["addr"], s["offset"], s["size"], s["entsize"], s["link"]))
# 动态符号
dynsym=[s for s in secs if s["sname"]=='.dynsym']
dynstr=[s for s in secs if s["sname"]=='.dynstr']
plt=[s for s in secs if s["sname"]=='.plt']
relplt=[s for s in secs if s["sname"] in ('.rel.plt','.rela.plt')]
if not (dynsym and dynstr and plt and relplt):
    print("!! 缺少节"); sys.exit()
ds, dstr, pl, rp = dynsym[0], dynstr[0], plt[0], relplt[0]
def dynsym_name(idx):
    o=ds["offset"]+idx*16
    nm,val,size,info,other,shndx=struct.unpack_from("<IIIBBH", d, o)
    e=d.index(b"\x00", dstr["offset"]+nm)
    return d[dstr["offset"]+nm:e].decode("ascii","replace")
# 读重定位
entsize = rp["entsize"] or 8
n = rp["size"]//entsize
symlist=[]
for i in range(n):
    o=rp["offset"]+i*entsize
    if entsize==8:
        r_off, r_info = struct.unpack_from("<II", d, o)
    else:
        r_off, r_info, r_add = struct.unpack_from("<III", d, o)
    symi = r_info >> 8
    symlist.append(dynsym_name(symi))
print()
print("PLT 节 addr=0x%x size=%d   重定位项 %d" % (pl["addr"], pl["size"], n))
# ARM PLT: PLT0 = 20 B, 之后每项 12 B
print("=== PLT 桩 → 符号（前 20）===")
for i,nm in enumerate(symlist[:20]):
    a = pl["addr"] + 20 + i*12
    print("   0x%06x  ->  %s" % (a, nm))
# 保存映射
import json
mp={}
for i,nm in enumerate(symlist):
    a = pl["addr"] + 20 + i*12
    mp[a]=nm
open(r'D:\mydata\workspace\tools\plt_map.json','w').write(json.dumps(mp))
print()
print("总映射 %d 条，已存 tools/plt_map.json" % len(mp))
