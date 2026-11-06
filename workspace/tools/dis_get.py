
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
# symtab
sym={}
symtab=[s for s in secs if s["sname"]=='.symtab']
strtab=[s for s in secs if s["sname"]=='.strtab']
if symtab and strtab:
    st, sr = symtab[0], strtab[0]
    for i in range(st["size"]//16):
        o=st["offset"]+i*16
        nm,val,size,info,other,shndx=struct.unpack_from("<IIIBBH", d, o)
        if nm==0: continue
        e=d.index(b"\x00", sr["offset"]+nm)
        n2=d[sr["offset"]+nm:e].decode("ascii","replace")
        if shndx==0 or shndx>=len(secs): continue
        sec=secs[shndx]
        if sec["typ"]==8: continue
        fn = info & 0xf
        if fn==2 and val:      # FUNC
            sym[sec["addr"]+val]=n2
        elif shndx and size and sec["sname"] in ('.rodata','.data','.data.rel.ro','.bss'):
            sym.setdefault(sec["addr"]+val,n2)
plt=json.load(open(r'D:\mydata\workspace\tools\plt_map.json'))
plt={int(k,16):v for k,v in plt.items()}
# got slot -> symbol
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
    if e-o>120: return None
    b=d[o:e]
    try: return b.decode('utf-8')
    except: return b.decode('latin-1')
md=Cs(CS_ARCH_ARM, CS_MODE_THUMB); md.detail=True
def label(t, here):
    if t in plt: return "PLT:"+plt[t].split('(')[0][:70]
    if t in sym: return "FUN:"+sym[t].split('(')[0][:70]
    return None
def disasm(start, size, title):
    print("="*100); print("%s   @0x%x  (%d B)" % (title,start,size)); print("="*100)
    code=d[a2o(start&~1):a2o(start&~1)+size]
    ins=list(md.disasm(code, start&~1))
    pend=None
    for ins in ins:
        ann=""
        m=ins.mnemonic; ops=ins.op_str
        if m in ('bl','blx','b.w','b') and ops.startswith('#'):
            try: t=int(ops[1:],16)
            except: t=None
            if t is not None:
                L=label(t,ins.address)
                if L: ann="   ; -> "+L
        if m=='ldr' and '[pc' in ops:
            # literal value
            disp=None
            try:
                disp=int(ops.split('#')[-1].rstrip(']'),16)
            except: pass
            if disp is not None:
                lit=(ins.address+4)&~3
                if ins.address%4: lit=(ins.address+4)&~3
                la=((ins.address+4)&~3)+disp
                o=a2o(la)
                if o is not None:
                    v,=struct.unpack_from("<I", d, o)
                    rd=ops.split(',')[0].strip()
                    tgt=None
                    if v in gotmap: ann="   ; =GOT[%s]" % gotmap[v].split('(')[0][:60]
                    elif v in plt: ann="   ; =PLT %s" % plt[v].split('(')[0][:60]
                    elif v in sym: ann="   ; =&%s" % sym[v].split('(')[0][:60]
                    elif v < 0x1000000 and (a2o(v) is not None):
                        cs=cstr(v)
                        if cs and cs.isprintable(): ann="   ; =\"%s\"" % cs[:60]
                    else:
                        ann="   ; =0x%x" % v
                    pend=(rd, la, v)
                    print("  0x%06x  %-6s %-34s%s" % (ins.address,m,ops,ann)); continue
        if m=='add' and ops.endswith(', pc') and pend is not None:
            a=ins.address; pc=(a+4)&~3
            tgt=pend[2]+pc
            L=None
            if tgt in gotmap: L="GOT[%s]"%gotmap[tgt].split('(')[0][:60]
            elif tgt in sym: L="&"+sym[tgt].split('(')[0][:60]
            else:
                cs=cstr(tgt)
                if cs and cs.isprintable(): L='"'+cs[:70]+'"'
            if L: ann="   ; => %s" % L
            pend=None
        print("  0x%06x  %-6s %-34s%s" % (ins.address,m,ops,ann))
disasm(0xec03c, 1080, "DataSubProcess::parseAndReqGetServoParams")



