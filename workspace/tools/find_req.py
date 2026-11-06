
import struct, capstone, re
p = r'D:\software\dobot\V1.3.4-stable\RobotMaintenanceTools.exe'
d=open(p,'rb').read()
e=struct.unpack_from('<I',d,0x3c)[0]; coff=e+4
machine,nsec,ts,psym,nsym,optsize,chars=struct.unpack_from('<HHIIIHH',d,coff)
opt=coff+20; sectab=opt+optsize
secs=[]
for i in range(nsec):
    off=sectab+i*40
    name=d[off:off+8].rstrip(b'\x00').decode('latin-1')
    vsize,va,rawsize,rawptr=struct.unpack_from('<IIII',d,off+8)
    secs.append((name,va,vsize,rawptr,rawsize))
def off2rva(o):
    for name,va,vsize,rawptr,rawsize in secs:
        if rawptr<=o<rawptr+rawsize: return va+(o-rawptr)
    return None
def rva2off(rva):
    for name,va,vsize,rawptr,rawsize in secs:
        if va<=rva<va+max(vsize,rawsize): return rawptr+(rva-va)
    return None
# 目标字符串 RVA
tgts={}
for s in (b'/settings/readServoParams', b'/settings/modifyServoParams', b'/servoParams', b'/config/servoReadOnlyAddress'):
    i=d.find(s)
    if i<0: continue
    r=off2rva(i)
    tgts[s.decode()]=r
    print("%-32s file@0x%x rva=0x%x" % (s.decode(), i, r))
print()
st=psym+nsym*18
def getname(o8):
    if o8[:4]==b'\x00\x00\x00\x00':
        o=struct.unpack_from('<I',o8,4)[0]; en=d.index(b'\x00',st+o); return d[st+o:en].decode('latin-1')
    return o8.rstrip(b'\x00').decode('latin-1')
syms=[]
for i in range(nsym):
    off=psym+i*18; nm=getname(d[off:off+8]); val,sec,typ,cls,naux=struct.unpack_from('<IhHBB',d,off+8)
    if 1<=sec<=nsec: syms.append((sec,secs[sec-1][1]+val,val,nm))
t1=sorted(set((r,n) for s,r,v,n in syms if s==1))
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
res={}
for i,(rva,nm) in enumerate(t1):
    nxt = t1[i+1][0] if i+1<len(t1) else rva+0x400
    if nxt<=rva: continue
    o=rva2off(rva)
    if o is None: continue
    for ins in md.disasm(d[o:o+min(nxt-rva,0x4000)], rva):
        for k,r in tgts.items():
            if ('0x%x'%(0x400000+r)) in ins.op_str:
                res.setdefault(k,[]).append((ins.address,nm,ins.mnemonic+' '+ins.op_str))
for k,v in res.items():
    print("=== %s : %d 处 ===" % (k,len(v)))
    for a,nm,txt in v[:8]:
        print("   0x%06x  %-56s %s" % (a,nm[:54],txt))
