
import struct, json
from capstone import *
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
st, sr = [s for s in secs if s["sname"]=='.symtab'][0], [s for s in secs if s["sname"]=='.strtab'][0]
want={}
for i in range(st["size"]//16):
    o=st["offset"]+i*16
    nm,val,size,info,other,shndx=struct.unpack_from("<IIIBBH", d, o)
    if nm==0 or shndx==0 or shndx>=len(secs): continue
    e=d.index(b"\x00", sr["offset"]+nm)
    n2=d[sr["offset"]+nm:e].decode("ascii","replace")
    if 'GetIndexFromAddr' in n2 or 'IndexFromAddr' in n2 or 'AddrFromIndex' in n2:
        want[secs[shndx]["addr"]+val]=(n2,size)
for a,(n2,sz) in sorted(want.items()):
    print("  @0x%x size=%d  %s" % (a,sz,n2))
print()
plt={int(k,16):v for k,v in json.load(open(r'D:\mydata\workspace\tools\plt_map.json')).items()}
def a2o(addr):
    for s in secs:
        if s["typ"]!=8 and s["addr"]<=addr<s["addr"]+s["size"]:
            return s["offset"]+(addr-s["addr"])
    return None
def cstr(a):
    o=a2o(a)
    if o is None: return None
    try: e=d.index(b"\x00", o)
    except: return None
    if e-o>200: return None
    b=d[o:e]
    try: t=b.decode('utf-8')
    except: return b.decode('latin-1')
    return t
md=Cs(CS_ARCH_ARM, CS_MODE_THUMB)
addrs=sorted(want)
start = addrs[0] & ~1
size = 420
code=d[a2o(start):a2o(start)+size]
ins=list(md.disasm(code,start))
pends={}
for i in ins:
    a=i.address; ann=""
    m=i.mnemonic; ops=i.op_str
    parts=[x.strip() for x in ops.split(',')] if ops else []
    if m in ('bl','blx') and ops.startswith('#'):
        t=int(ops[1:],16)
        if t in plt: ann="   ; -> "+plt[t].split('(')[0][:70]
    if m=='ldr' and len(parts)==2 and parts[1].startswith('[pc'):
        try: disp=int(parts[1].split('#')[-1].rstrip(']'),16)
        except: disp=None
        if disp is not None:
            la=((a+4)&~3)+disp
            o=a2o(la)
            if o is not None:
                v,=struct.unpack_from("<I", d, o)
                cs=cstr(v)
                if cs and len(cs)>0: ann="   ; =\"%s\""%cs[:70]
                else: ann="   ; =0x%x"%v
                pends[parts[0]]=v
    if m=='add' and len(parts)==2 and parts[1]=='pc' and parts[0] in pends:
        v=pends.pop(parts[0]); tgt=(v+((a+4)&~3))&0xffffffff
        cs=cstr(tgt)
        if cs and len(cs)>0: ann="   ; => \"%s\""%cs[:80]
        else: ann="   ; => 0x%x"%tgt
    print("  0x%06x  %-7s %-30s%s" % (a,m,ops,ann))
