
import struct, capstone, re, sys
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
def rva2off(rva):
    for name,va,vsize,rawptr,rawsize in secs:
        if va<=rva<va+max(vsize,rawsize): return rawptr+(rva-va)
    return None
st=psym+nsym*18
def getname(o8):
    if o8[:4]==b'\x00\x00\x00\x00':
        o=struct.unpack_from('<I',o8,4)[0]; en=d.index(b'\x00',st+o); return d[st+o:en].decode('latin-1')
    return o8.rstrip(b'\x00').decode('latin-1')
t1=[]
for i in range(nsym):
    off=psym+i*18; nm=getname(d[off:off+8]); val,sec,typ,cls,naux=struct.unpack_from('<IhHBB',d,off+8)
    if sec==1: t1.append((secs[0][1]+val, nm))
t1.sort()
def sym_at(rva):
    best=None
    for r,n in t1:
        if r<=rva: best=(r,n)
        else: break
    return best
TARGETS={0x47ad40:'postSettingsReadServoParams', 0x47b560:'postSettingsModifyServoParams'}
res={k:[] for k in TARGETS}
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
scanned=0
for i,(rva,nm) in enumerate(t1):
    nxt = t1[i+1][0] if i+1<len(t1) else rva+0x400
    if nxt<=rva or nxt-rva>0x4000: continue
    o=rva2off(rva)
    if o is None: continue
    for ins in md.disasm(d[o:o+(nxt-rva)], rva):
        scanned+=1
        for k,name in TARGETS.items():
            if ('0x%x'%k) in ins.op_str:
                res[k].append((ins.address, sym_at(rva)[1], ins.mnemonic+' '+ins.op_str))
print("扫描指令", scanned)
for k,name in TARGETS.items():
    print("=== %s (0x%x) : %d 处 ===" % (name,k,len(res[k])))
    for a,fn,txt in res[k][:15]:
        print("   0x%06x  %-58s %s" % (a, fn[:56], txt))
