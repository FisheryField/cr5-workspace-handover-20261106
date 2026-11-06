
import struct
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
st, sr = S['.symtab'], S['.strtab']
print("symtab entsize=%d size=%d  -> 条目 %d" % (st["entsize"], st["size"], st["size"]//16))
print()
for i in range(st["size"]//16):
    o=st["offset"]+i*16
    nm,val,size,info,other,shndx=struct.unpack_from("<IIIBBH", d, o)
    if nm==0: continue
    e=d.index(b"\x00", sr["offset"]+nm)
    n2=d[sr["offset"]+nm:e].decode("ascii","replace")
    if n2.startswith('_ZN14DataSubProcess7readSDO') or n2.startswith('_ZN14DataSubProcess7getAndPack') or n2.startswith('_ZN14DataSubProcess25parseAndReqGet'):
        sec = secs[shndx] if shndx < len(secs) else None
        print("  name=%s" % n2)
        print("     shndx=%d  value=0x%x  size=%d  info=0x%x" % (shndx, val, size, info))
        if sec: print("     section=%s addr=0x%x size=0x%x  -> 绝对=0x%x" % (sec["sname"], sec["addr"], sec["size"], sec["addr"]+val))
print()
print("=== 0x1a81d0..0x1a8210 的字节（每 2 字节）===")
for a in range(0x1a81d0,0x1a8212,2):
    w,=struct.unpack_from("<H", d, a2o(a))
    print("   0x%06x  %04x" % (a,w))
print()
print("=== 从 0x1a81f0 反汇编 ===")
md=Cs(CS_ARCH_ARM, CS_MODE_THUMB)
code=d[a2o(0x1a81e0):a2o(0x1a81e0)+0x60]
for i in md.disasm(code,0x1a81e0):
    print("   0x%06x  %-8s %s" % (i.address,i.mnemonic,i.op_str))
