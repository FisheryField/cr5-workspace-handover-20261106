
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
def rva2off(rva):
    for name,va,vsize,rawptr,rawsize in secs:
        if va<=rva<va+max(vsize,rawsize): return rawptr+(rva-va)
    return None
def cstr(rva,n=70):
    o=rva2off(rva)
    if o is None: return None
    en=d.index(b'\x00',o,o+n); raw=d[o:en]
    return raw.decode('utf-8','replace') if len(raw)>0 else None
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
tmap=dict(t1)
def nexxt(rva):
    for r,n in t1:
        if r>rva: return r
    return rva+0x400
def sym_at(rva):
    # 最近的 <= rva 的符号
    best=None
    for r,n in t1:
        if r<=rva: best=(r,n)
        else: break
    return best
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
LAM={'lambda#0':0x600f0,'lambda#1':0x61670,'lambda#4':0x624a0,'lambda#5':0x63dc0}
for label,rva in LAM.items():
    n=nexxt(rva)-rva
    print("="*80)
    print("%s   RVA=0x%x  size=%d" % (label, rva, n))
    print("="*80)
    o=rva2off(rva)
    cnt=0
    for ins in md.disasm(d[o:o+n], rva):
        note=""
        for m in re.finditer(r'0x(5[0-9a-f]{5})', ins.op_str):
            v=int(m.group(1),16)
            if 0x540000<=v<=0x599999:
                s=cstr(v-0x400000,60)
                if s: note='  ; "%s"' % s
        if not note and ins.mnemonic in ('call','jmp') and ins.op_str.startswith('0x'):
            t=int(ins.op_str,16)
            if 0x400000<=t<0x600000:
                sa=sym_at(t-0x400000)
                if sa: note='  ; -> %s' % sa[1][:60]
        if note:
            print("  0x%06x  %-16s %-30s%s" % (ins.address, ins.bytes.hex(), ins.mnemonic+' '+ins.op_str, note))
        cnt+=1
        if cnt>300: print("  ...(截断)"); break
    print()
