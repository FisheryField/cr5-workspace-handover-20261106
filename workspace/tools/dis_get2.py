
import struct, json, sys
from capstone import *
from capstone.arm import *
P = r"D:\mydata\workspace\libdataSvr.so.bin"
d = open(P,'rb').read()
e_shoff, = struct.unpack_from("<I", d, 32)
e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", d, 46)
def sh(i):
    o=e_shoff+i*e_shentsize
    n,t,f,a,off,sz,lk,inf,al,ent = struct.unpack_from("<IIIIIIIIII", d, o)
    return dict(idx=i,name=n,typ=t,flags=f,addr=a,offset=off,size=sz,link=lk,entsize=ent)
secs=[sh(i) for i in range(e_shnum)]
shstr=secs[e_shstrndx]
def sname(n):
    e=d.index(b"\x00", shstr["offset"]+n); return d[shstr["offset"]+n:e].decode("ascii","replace")
for s in secs: s["sname"]=sname(s["name"])
S={}
for s in secs: S.setdefault(s["sname"], s)
def a2o(addr):
    for s in secs:
        if s["typ"]!=8 and s["addr"]<=addr<s["addr"]+s["size"]:
            return s["offset"]+(addr-s["addr"])
    return None
sym={}
st, sr = S['.symtab'], S['.strtab']
for i in range(st["size"]//16):
    o=st["offset"]+i*16
    nm,val,size,info,other,shndx=struct.unpack_from("<IIIBBH", d, o)
    if nm==0 or shndx==0 or shndx>=len(secs): continue
    sec=secs[shndx]
    if sec["typ"]==8: continue
    e=d.index(b"\x00", sr["offset"]+nm)
    n2=d[sr["offset"]+nm:e].decode("ascii","replace")
    fn = info & 0xf
    if fn==2 and val: sym.setdefault(sec["addr"]+val, n2)
plt={int(k,16):v for k,v in json.load(open(r'D:\mydata\workspace\tools\plt_map.json')).items()}
gotmap={}
ds,dstr=S['.dynsym'],S['.dynstr']
def dynsym_name(idx):
    o=ds["offset"]+idx*16
    nm,val,size,info,other,shndx=struct.unpack_from("<IIIBBH", d, o)
    e=d.index(b"\x00", dstr["offset"]+nm)
    return d[dstr["offset"]+nm:e].decode("ascii","replace")
rp=S['.rel.plt']
for i in range(rp["size"]//8):
    r_off,r_info=struct.unpack_from("<II", d, rp["offset"]+i*8)
    gotmap[r_off]=dynsym_name(r_info>>8)
def cstr(a):
    o=a2o(a)
    if o is None: return None
    e=d.index(b"\x00", o)
    if e-o>140: return None
    b=d[o:e]
    try: return b.decode('utf-8')
    except: return b.decode('latin-1')
def short(n): return n.split('(')[0][:78]
md=Cs(CS_ARCH_ARM, CS_MODE_THUMB); md.detail=True
out=[]
def disasm(start,size,title):
    out.append("="*110)
    out.append("%s  @0x%x (%d B)" % (title,start,size))
    out.append("="*110)
    code=d[a2o(start):a2o(start)+size]
    pend=None
    for ins in md.disasm(code,start):
        ann=""; m=ins.mnemonic; ops=ins.op_str
        if m in ('bl','blx') and ops.startswith('#'):
            try: t=int(ops[1:],16)
            except: t=None
            if t is not None:
                if t in plt: ann="   ; -> "+short(plt[t])
                elif t in sym: ann="   ; -> "+short(sym[t])
        if m=='ldr' and '[pc' in ops:
            try: disp=int(ops.split('#')[-1].rstrip(']'),16)
            except: disp=None
            if disp is not None:
                la=((ins.address+4)&~3)+disp
                o=a2o(la)
                if o is not None:
                    v,=struct.unpack_from("<I", d, o)
                    rd=ops.split(',')[0].strip()
                    if v in gotmap: ann="   ; GOT<%s>" % short(gotmap[v])
                    elif v in plt: ann="   ; =PLT %s" % short(plt[v])
                    elif v in sym: ann="   ; =&%s" % short(sym[v])
                    else:
                        cs=cstr(v)
                        if cs and cs.isprintable() and len(cs)>1: ann="   ; =\"%s\"" % cs[:70]
                        else: ann="   ; =0x%x" % v
                    pend=(rd,v)
                    out.append("  0x%06x  %-7s %-32s%s" % (ins.address,m,ops,ann)); continue
        if m=='add' and (ops.endswith(', pc') or ', pc' in ops) and pend is not None:
            pc=(ins.address+4)&~3
            tgt=pend[1]+pc
            L=None
            if tgt in gotmap: L="GOT<"+short(gotmap[tgt])+">"
            elif tgt in sym: L="&"+short(sym[tgt])
            else:
                cs=cstr(tgt)
                if cs and cs.isprintable() and len(cs)>1: L='"'+cs[:80]+'"'
            if L: ann="   ; => %s" % L
            pend=None
        out.append("  0x%06x  %-7s %-32s%s" % (ins.address,m,ops,ann))
disasm(0xec03c,1080,"parseAndReqGetServoParams")
open(r'D:\mydata\workspace\tools\out_get.txt','w',encoding='utf-8').write("\n".join(out))
print("lines:",len(out))
