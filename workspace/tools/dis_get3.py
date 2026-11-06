
import struct, json
from capstone import *
from capstone.arm import *
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
    if (info&0xf)==2 and val: sym.setdefault(sec["addr"]+val, n2)
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
GOTLO, GOTHI = S['.got']["addr"], S['.got']["addr"]+S['.got']["size"]
# 本库自有全局（symtab 里 .bss/.data 的对象）也建表
glob={}
for i in range(st["size"]//16):
    o=st["offset"]+i*16
    nm,val,size,info,other,shndx=struct.unpack_from("<IIIBBH", d, o)
    if nm==0 or shndx==0 or shndx>=len(secs): continue
    sec=secs[shndx]
    if sec["sname"] not in ('.bss','.data','.data.rel.ro'): continue
    e=d.index(b"\x00", sr["offset"]+nm)
    glob.setdefault(sec["addr"]+val, d[sr["offset"]+nm:e].decode("ascii","replace"))
def cstr(a):
    o=a2o(a)
    if o is None: return None
    try: e=d.index(b"\x00", o)
    except: return None
    if e-o>160: return None
    b=d[o:e]
    try: t=b.decode('utf-8')
    except: return b.decode('latin-1')
    return t if t.isprintable() else None
def name_got(a):
    if a in gotmap: return "GOT["+gotmap[a].split('(')[0][:64]+"]"
    if a in glob: return "GLOB["+glob[a].split('(')[0][:64]+"]"
    return None
md=Cs(CS_ARCH_ARM, CS_MODE_THUMB); md.detail=True
out=[]
def disasm(start,size,title):
    out.append("="*112); out.append("%s  @0x%x (%d B)"%(title,start,size)); out.append("="*112)
    code=d[a2o(start):a2o(start)+size]
    reg={}   # regname -> ('got',addr) | ('addr',a) | ('const',v) | ('straddr',a)
    pends={}
    for ins in md.disasm(code,start):
        ann=""; m=ins.mnemonic; ops=ins.op_str
        a=ins.address
        parts=[x.strip() for x in ops.split(',')] if ops else []
        def setr(r,v):
            nonlocal reg
            if r: reg[r]=v
        # bl / blx 直接调用
        if m in ('bl','blx') and ops.startswith('#'):
            try: t=int(ops[1:],16)
            except: t=None
            if t is not None:
                if t in plt: ann="   ; -> "+plt[t].split('(')[0][:76]
                elif t in sym: ann="   ; -> "+sym[t].split('(')[0][:76]
            out.append("  0x%06x  %-7s %-32s%s"%(a,m,ops,ann)); reg={}; pends={}; continue
        # ldr rX,[pc,#d]  -> 记录 pending 并解析字面量
        if m=='ldr' and len(parts)==2 and parts[1].startswith('[pc'):
            rd=parts[0]
            try: disp=int(parts[1].split('#')[-1].rstrip(']'),16)
            except: disp=None
            if disp is not None:
                la=((a+4)&~3)+disp
                o=a2o(la)
                if o is not None:
                    v,=struct.unpack_from("<I", d, o)
                    sg=name_got(v)
                    if sg: ann="   ; ="+sg
                    else:
                        cs=cstr(v)
                        if cs and len(cs)>1: ann="   ; =\"%s\""%cs[:72]
                        else: ann="   ; =0x%x"%v
                    pends[rd]=(v, la)
                    out.append("  0x%06x  %-7s %-32s%s"%(a,m,ops,ann)); continue
        # add rX, pc  -> 结算 pending
        if m=='add' and len(parts)==2 and parts[1]=='pc' and parts[0] in pends:
            v,la = pends.pop(parts[0])
            tgt=(v+((a+4)&~3))&0xffffffff
            L=name_got(tgt)
            if not L:
                cs=cstr(tgt)
                if cs and len(cs)>1: L='"'+cs[:84]+'"'
            if L:
                out.append("  0x%06x  %-7s %-32s   ; => %s"%(a,m,ops,L))
                setr(parts[0], ('addr',tgt))
                continue
        # ldr rY,[rX, rZ] / str rY,[rX, rZ]  -> GOT 索引寻址
        if m in ('ldr','str','ldrb','strb') and len(parts)==2 and parts[1].startswith('[') and parts[1].endswith(']'):
            inner=parts[1][1:-1]
            if ',' in inner:
                base, idx = [x.strip() for x in inner.split(',')]
                bv=reg.get(base); iv=reg.get(idx)
                if bv and bv[0]=='got' and iv and iv[0]=='const':
                    tgt=bv[1]+iv[1]
                    L=name_got(tgt)
                    if L: ann="   ; ** %s"%L
                    else: ann="   ; ** 0x%x"%tgt
        out.append("  0x%06x  %-7s %-32s%s"%(a,m,ops,ann))
        # 更新寄存器模型
        if m in ('movs','mov','mov.w') and len(parts)==2:
            try: setr(parts[0],('const',int(parts[1].lstrip('#'),16) if parts[1].startswith('#') else 0))
            except: pass
        if m in ('movw','mov') and len(parts)==2 and parts[1].startswith('#'):
            try: setr(parts[0],('const',int(parts[1][1:],16)))
            except: pass
        if m=='ldr' and len(parts)==2 and parts[1]=='[r6, r3]':
            pass
        if m=='ldr' and len(parts)==2 and parts[1].startswith('[r6'):
            inner=parts[1][1:-1]
            if ',' in inner:
                idx=inner.split(',')[1].strip()
                iv=reg.get(idx)
                if iv and iv[0]=='const' and reg.get('r6',(None,))[0]=='got':
                    setr(parts[0],('got',(reg['r6'][1]+iv[1])&0xffffffff))
disasm(0xec03c,1080,"parseAndReqGetServoParams")
open(r'D:\mydata\workspace\tools\out_get2.txt','w',encoding='utf-8').write("\n".join(out))
print("ok",len(out))
