
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
    if 1 <= sec <= nsec:
        syms.append((sec, secs[sec-1][1]+val, val, nm))
syms.sort(key=lambda x:(x[0],x[2]))
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def nextin(sec, voff):
    for s,r,v,n in syms:
        if s==sec and v>voff: return v
    return None
def dis(sec, voff, label, limit=0x400):
    rva = secs[sec-1][1] + voff
    nv = nextin(sec, voff)
    endv = nv if nv and nv-voff<=limit else voff+limit
    o=rva2off(rva); code=d[o:o+(endv-voff)]
    print("="*76); print("%s   RVA=0x%x  size=%d" % (label, rva, len(code))); print("="*76)
    for ins in md.disasm(code, rva):
        print("  0x%06x  %-18s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
dis(1, 0x4b80, "CommonData::getRandom()", 0x300)
