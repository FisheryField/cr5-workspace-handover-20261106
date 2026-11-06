
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
def nexxt(rva):
    for r,n in t1:
        if r>rva: return r
    return rva+0x300
def cstr(rva, n=70):
    o=rva2off(rva)
    if o is None: return None
    en=d.index(b'\x00',o,o+n)
    raw=d[o:en]
    if len(raw)<1: return None
    try: return raw.decode('utf-8')
    except Exception: return raw.decode('latin-1')
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def dis(rva, label, limit=0x300):
    end=nexxt(rva); n=end-rva
    if n>limit: n=limit
    o=rva2off(rva)
    print("="*78); print("%s  RVA=0x%x size=%d" % (label,rva,n)); print("="*78)
    for ins in md.disasm(d[o:o+n], rva):
        note=""
        for m in re.finditer(r'0x(5[0-9a-f]{5})', ins.op_str):
            v=int(m.group(1),16)
            if 0x540000 <= v <= 0x560000:
                s=cstr(v-0x400000, 60)
                if s: note='   ; "%s"' % s
        print("  0x%06x  %-16s %-34s%s" % (ins.address, ins.bytes.hex(), ins.mnemonic+' '+ins.op_str, note))
dis(0x7ad40, "DobotProtocol::postSettingsReadServoParams", 0x300)
