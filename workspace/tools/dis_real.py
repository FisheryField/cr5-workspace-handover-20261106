
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
# 娉ㄦ剰锛歏alue 鍗崇粷瀵瑰湴鍧€锛屼笉鍔?section 鍩哄潃
sym={}; symsz={}
st, sr = S['.symtab'], S['.strtab']
for i in range(st["size"]//16):
    o=st["offset"]+i*16
    nm,val,size,info,other,shndx=struct.unpack_from("<IIIBBH", d, o)
    if nm==0 or shndx==0 or shndx>=len(secs): continue
    e=d.index(b"\x00", sr["offset"]+nm)
    n2=d[sr["offset"]+nm:e].decode("ascii","replace")
    if (info&0xf)==2 and val:
        sym.setdefault(val&~1, n2); symsz[val&~1]=size
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
def short(n): return n.split('(')[0][:74]
def enc(a):
    best=None
    for k in sym:
        if k<=a and (best is None or k>best): best=k
    return (best, sym[best]) if best is not None else (0,'?')
md=Cs(CS_ARCH_ARM, CS_MODE_THUMB)
def dis(start,size,title):
    start&=~1
    print("="*106); print("%s @0x%x (%d B)"%(title,start,size)); print("="*106)
    code=d[a2o(start):a2o(start)+size]
    pends={}
    for i in md.disasm(code,start):
        a=i.address; m=i.mnemonic; ops=i.op_str; ann=""
        parts=[x.strip() for x in ops.split(',')] if ops else []
        if m in ('bl','blx') and ops.startswith('#'):
            t=int(ops[1:],16)
            if t in plt: ann="   ; -> "+short(plt[t])
            elif t in sym: ann="   ; -> "+short(sym[t])
        if m=='ldr' and len(parts)==2 and parts[1].startswith('[pc'):
            try:
                disp=int(parts[1].split('#')[-1].rstrip(']'),16)
                la=((a+4)&~3)+disp
                o=a2o(la)
                if o is not None:
                    v,=struct.unpack_from("<I", d, o)
                    if v in gotmap: ann="   ; GOT<%s>"%short(gotmap[v])
                    else:
                        cs=cstr(v)
                        if cs and len(cs)>1: ann='   ; ="%s"'%cs[:64]
                        else: pends[parts[0]]=v
            except: pass
        if m=='add' and len(parts)==2 and parts[1]=='pc' and parts[0] in pends:
            v=pends.pop(parts[0]); tgt=(v+((a+4)&~3))&0xffffffff
            cs=cstr(tgt)
            if cs and len(cs)>1: ann='   ; => "%s"'%cs[:74]
            else: ann="   ; => 0x%x"%tgt
        print("  0x%06x  %-8s %-32s%s"%(a,m,ops,ann))
# 鐩爣绗﹀彿鐨勭湡瀹炲湴鍧€
for nm in ('_ZN14DataSubProcess7readSDOEPS_R8_SDOInfoi','_ZN14DataSubProcess8writeSDOEPS_8_SDOInfo',
           '_ZN14DataSubProcess21getAndPackServoParamsERSs','_ZN14DataSubProcess10readSDOthdEPS_Ss'):
    for k,v in sym.items():
        if v==nm: print("  %s @0x%x size=%d" % (nm,k,symsz[k]))
print()
# readSDO
addr=None
for k,v in sym.items():
    if v=='_ZN14DataSubProcess7readSDOEPS_R8_SDOInfoi': addr=k
dis(addr, symsz[addr], "DataSubProcess::readSDO")

