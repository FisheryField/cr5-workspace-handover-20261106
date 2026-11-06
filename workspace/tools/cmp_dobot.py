
import struct, re, sys
P = r"D:\mydata\workspace\data\libCmpDobot6Axes.so"
d = open(P,'rb').read()
print("大小 %d" % len(d))
assert d[:4]==b'\x7fELF'
print("class=%d data=%d machine=%d type=%d" % (d[4],d[5],struct.unpack_from("<H",d,18)[0],struct.unpack_from("<H",d,16)[0]))
e_shoff,=struct.unpack_from("<I",d,32)
e_shentsize,e_shnum,e_shstrndx=struct.unpack_from("<HHH",d,46)
secs=[]
for i in range(e_shnum):
    o=e_shoff+i*e_shentsize
    n,t,f,a,off,sz,lk,inf,al,ent=struct.unpack_from("<IIIIIIIIII",d,o)
    secs.append(dict(name=n,typ=t,addr=a,off=off,size=sz,link=lk,ent=ent))
shstr=secs[e_shstrndx]
def sn(x):
    if x["typ"]==8: return ".bss"
    if x["name"]==0: return ""
    s=shstr["off"]+x["name"]; e=d.index(b"\x00",s)
    return d[s:e].decode('latin-1')
for x in secs: x["sname"]=sn(x)
print("节:", ", ".join("%s(0x%x,%d)"%(x["sname"],x["addr"],x["size"]) for x in secs if x["sname"]))
print()
# 导出/动态符号
for sname in ('.dynsym','.symtab'):
    S=[x for x in secs if x["sname"]==sname]
    if not S: continue
    S=S[0]; strt=[x for x in secs if x["name"]==S["link"]]
    if not strt: continue
    strt=strt[0]
    n=S["size"]//(S["ent"] or 16)
    print("=== %s (%d 项) ===" % (sname, n))
    cnt=0
    for i in range(n):
        o=S["off"]+i*(S["ent"] or 16)
        nm,val,size,info,other,shndx=struct.unpack_from("<IIIBBH",d,o)
        if nm==0: continue
        s=strt["off"]+nm; e=d.index(b"\x00",s); t=d[s:e].decode('latin-1')
        print("   [%d] 0x%06x %s" % (i, val, t))
        cnt+=1
        if cnt>70: print("   ..."); break
    print()
print("=== 字符串 ===")
for m in re.finditer(rb'[\x20-\x7e]{4,120}', d):
    s=m.group().decode('latin-1')
    if any(k in s.lower() for k in ('sdo','servo','param','robot','axis','dobot','ethercat','shm','mailbox')):
        print("   0x%06x  %s" % (m.start(), s[:110]))
