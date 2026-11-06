
import struct, capstone
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
def readcstr(rva, n=80):
    o=rva2off(rva)
    if o is None: return None
    end=d.index(b'\x00', o, o+n)
    return d[o:end]
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
def enclosing(rva):
    best=None
    for r,n in t1:
        if r<=rva: best=(r,n)
        else: break
    return best
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
for tag in (0x7b120, 0x7b217, 0x7b9a5):
    sv,sn = enclosing(tag)
    nv=None
    for r,n in t1:
        if r>sv: nv=r; break
    print("="*78); print("%s  start RVA=0x%x  (xref@0x%x)" % (sn, sv, tag)); print("="*78)
    o=rva2off(sv)
    for ins in md.disasm(d[o:o+min((nv or sv+0x300)-sv, 0x300)], sv):
        mk=""
        if ins.address in (tag,): mk="   <<<"
        print("  0x%06x  %-16s %s %s%s" % (ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str,mk))
        if '0x54' in ins.op_str and 'esp' in ins.op_str:
            import re
            for mm in re.finditer(r'0x(54[0-9a-f]{4})', ins.op_str):
                v=int(mm.group(1),16)
                s=readcstr(v-0x400000, 60)
                if s: print("             ; \"%s\"" % s.decode('utf-8','replace'))
