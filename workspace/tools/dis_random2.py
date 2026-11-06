
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
rows=[]
for i in range(nsym):
    off=psym+i*18; nm=getname(d[off:off+8]); val,sec,typ,cls,naux=struct.unpack_from('<IhHBB',d,off+8)
    rows.append((sec,val,nm))
print("=== 0x6a000..0x6c200 区间的符号 ===")
for sec,val,nm in sorted(rows):
    if sec==1 and 0x6a000<=val<=0x6c200:
        print("   0x%06x  %s" % (val, nm))
print()
print("=== 从 0x6afbe 正向反汇编 ===")
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
o=rva2off(0x6afbe); code=d[o:o+0x260]
for ins in md.disasm(code, 0x6afbe):
    print("  0x%06x  %-18s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
