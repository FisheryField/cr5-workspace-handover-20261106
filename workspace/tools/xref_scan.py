
import struct, capstone
p = r'D:\software\dobot\V1.3.4-stable\RobotMaintenanceTools.exe'
d=open(p,'rb').read()
e=struct.unpack_from('<I',d,0x3c)[0]; coff=e+4
machine,nsec,ts,psym,nsym,optsize,chars=struct.unpack_from('<HHIIIHH',d,coff)
opt=coff+20; imgbase=struct.unpack_from('<I',d,opt+28)[0]; sectab=opt+optsize
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
syms=[]
for i in range(nsym):
    off=psym+i*18; nm=getname(d[off:off+8]); val,sec,typ,cls,naux=struct.unpack_from('<IhHBB',d,off+8)
    if 1<=sec<=nsec: syms.append((sec, secs[sec-1][1]+val, val, nm))
t1=sorted(set((r,n) for s,r,v,n in syms if s==1))
tv=[r for r,n in t1]
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail=False
TARGETS={0x5af5d0:'_g_strServoParamsPassword', 0x54cacc:'"Random code: %1"'}
import bisect
res={k:[] for k in TARGETS}
tot=0
for i,(rva,nm) in enumerate(t1):
    nxt = t1[i+1][0] if i+1<len(t1) else rva+0x400
    if nxt<=rva: continue
    o=rva2off(rva)
    if o is None: continue
    code=d[o:o+min(nxt-rva, 0x4000)]
    if not code: continue
    for ins in md.disasm(code, rva):
        tot+=1
        op=ins.op_str
        if '0x' in op:
            for t,name in TARGETS.items():
                if ('0x%x'%t) in op:
                    res[t].append((ins.address, nm, ins.mnemonic+' '+op))
print("扫描指令数 =", tot)
for t,name in TARGETS.items():
    print("=== %s (0x%x) : %d 处 ===" % (name,t,len(res[t])))
    for a,nm,txt in res[t][:15]:
        print("   0x%06x  in %s   %s" % (a,nm,txt))
