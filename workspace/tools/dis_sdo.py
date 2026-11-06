
import struct, json, sys
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
sym={}
st, sr = S['.symtab'], S['.strtab']
for i in range(st["size"]//16):
    o=st["offset"]+i*16
    nm,val,size,info,other,shndx=struct.unpack_from("<IIIBBH", d, o)
    if nm==0 or shndx==0 or shndx>=len(secs): continue
    sec=secs[shndx]
    if sec["typ"]==8:
        continue
    e=d.index(b"\x00", sr["offset"]+nm)
    n2=d[sr["offset"]+nm:e].decode("ascii","replace")
    if (info&0xf)==2 and val: sym[sec["addr"]+val]=n2
plt={int(k,16):v for k,v in json.load(open(r'D:\mydata\workspace\tools\plt_map.json')).items()}
gotmap={}
ds,dstr=S['.dynsym'],S['.dynstr']
def dsn(idx):
    o=ds["offset"]+idx*16
    nm,val,size,info,other,shndx=struct.unpack_from("<IIIBBH", d, o)
    e=d.index(b"\x00", dstr["offset"]+nm)
    return d[dstr["offset"]+nm:e].decode("ascii","replace")
rp=S['.rel.plt']
for i in range(rp["size"]//8):
    r_off,r_info=struct.unpack_from("<II", d, rp["offset"]+i*8)
    gotmap[r_off]=dsn(r_info>>8)
def cstr(a):
    o=a2o(a)
    if o is None: return None
    try: e=d.index(b"\x00", o)
    except: return None
    if e-o>200: return None
    b=d[o:e]
    try: t=b.decode('utf-8')
    except: return b.decode('latin-1')
    return t if t.isprintable() else None
md=Cs(CS_ARCH_ARM, CS_MODE_THUMB)
def dis(start,size,title):
    start &= ~1
    print("="*104); print("%s @0x%x (%d B)"%(title,start,size)); print("="*104)
    code=d[a2o(start):a2o(start)+size]
    for i in md.disasm(code,start):
        a=i.address; m=i.mnemonic; ops=i.op_str; ann=""
        if m in ('bl','blx') and ops.startswith('#'):
            t=int(ops[1:],16)
            if t in plt: ann="   ; -> "+plt[t].split('(')[0][:74]
            elif t in sym: ann="   ; -> "+sym[t].split('(')[0][:74]
        if m=='ldr' and '[pc' in ops:
            try:
                disp=int(ops.split('#')[-1].rstrip(']'),16)
                la=((a+4)&~3)+disp
                o=a2o(la)
                if o is not None:
                    v,=struct.unpack_from("<I", d, o)
                    if v in gotmap: ann="   ; GOT<%s>"%gotmap[v].split('(')[0][:58]
                    elif v in plt: ann="   ; PLT %s"%plt[v].split('(')[0][:58]
                    else:
                        cs=cstr(v)
                        if cs and len(cs)>1: ann='   ; ="%s"'%cs[:66]
            except: pass
        print("  0x%06x  %-8s %-30s%s"%(a,m,ops,ann))
dis(0x1a81fd,232,"DataSubProcess::readSDO(DataSubProcess*, SDOInfo&, int)")
dis(0x1a9159,164,"DataSubProcess::readSDOthd(DataSubProcess*, std::string)")
