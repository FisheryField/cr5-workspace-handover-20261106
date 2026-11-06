
import struct, json
from capstone import *
P = r"D:\mydata\workspace\libdataSvr.so.bin"
d=open(P,'rb').read()
e_shoff,=struct.unpack_from("<I",d,32); e_shentsize,e_shnum,e_shstrndx=struct.unpack_from("<HHH",d,46)
secs=[]
for i in range(e_shnum):
    o=e_shoff+i*e_shentsize
    n,t,f,a,off,sz,lk,inf,al,ent=struct.unpack_from("<IIIIIIIIII",d,o)
    secs.append(dict(name=n,typ=t,addr=a,off=off,size=sz,link=lk,ent=ent))
shstr=secs[e_shstrndx]
def sn(x):
    if x["name"]==0: return ""
    s=shstr["off"]+x["name"]; e=d.index(b"\x00",s); return d[s:e].decode('latin-1')
for x in secs: x["sname"]=sn(x)
S={}
for x in secs: S.setdefault(x["sname"],x)
def a2o(a):
    for x in secs:
        if x["typ"]!=8 and x["addr"]<=a<x["addr"]+x["size"]: return x["off"]+(a-x["addr"])
    return None
st=S['.symtab']; strt=S['.strtab']; sym={}
for i in range(st["size"]//16):
    o=st["off"]+i*16
    nm,val,size,info,other,shndx=struct.unpack_from("<IIIBBH",d,o)
    if nm==0 or shndx==0 or shndx>=len(secs): continue
    e=d.index(b"\x00",strt["off"]+nm)
    n2=d[strt["off"]+nm:e].decode('latin-1')
    if (info&0xf)==2 and val: sym.setdefault(val&~1,n2); sym['sz'+str(val&~1)]=size
plt={int(k,16):v for k,v in json.load(open(r'D:\mydata\workspace\tools\plt_map.json')).items()}
def cstr(a):
    o=a2o(a)
    if o is None: return None
    try: e=d.index(b"\x00",o)
    except: return None
    if e-o>150: return None
    b=d[o:e]
    try: t=b.decode('utf-8')
    except: return b.decode('latin-1')
    return t if t.isprintable() else None
md=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
def dis(start,size,title,limit=200):
    start&=~1
    print("="*100); print("%s @0x%x (%d B)"%(title,start,size)); print("="*100)
    code=d[a2o(start):a2o(start)+size]; pend={}; n=0
    for i in md.disasm(code,start):
        a=i.address; m=i.mnemonic; ops=i.op_str; ann=""
        parts=[x.strip() for x in ops.split(',')] if ops else []
        if m in ('bl','blx') and ops.startswith('#'):
            t=int(ops[1:],16)
            if t in plt: ann="   ; -> "+plt[t].split('(')[0][:66]
            elif t in sym: ann="   ; -> "+sym[t].split('(')[0][:66]
        if m=='ldr' and len(parts)==2 and parts[1].startswith('[pc'):
            try:
                disp=int(parts[1].split('#')[-1].rstrip(']'),16)
                la=((a+4)&~3)+disp; o=a2o(la)
                if o is not None:
                    v,=struct.unpack_from("<I",d,o)
                    cs=cstr(v)
                    if cs and len(cs)>1: ann='   ; ="%s"'%cs[:70]
                    pend[parts[0]]=v
            except: pass
        if m=='add' and len(parts)==2 and parts[1]=='pc' and parts[0] in pend:
            v=pend.pop(parts[0]); tgt=(v+((a+4)&~3))&0xffffffff
            cs=cstr(tgt)
            if cs and len(cs)>1: ann='   ; => "%s"'%cs[:80]
        print("  0x%06x  %-7s %-32s%s"%(a,m,ops,ann))
        n+=1
        if n>=limit: print("   ..."); break
target=None
for k,v in sym.items():
    if isinstance(k,str): continue
    if v=='_ZN14DataSubProcess17modifyServoParamsEP14evhttp_requestPv': target=k
print("modifyServoParams @0x%x size=%s" % (target, sym.get('sz'+str(target))))
dis(target, sym['sz'+str(target)], "modifyServoParams", 150)
