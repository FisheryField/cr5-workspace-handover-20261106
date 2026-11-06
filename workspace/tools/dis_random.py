
import struct, sys, capstone
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
    if sec==1: syms.append((val,nm))
syms.sort()
def enclosing(v):
    best=None
    for val,nm in syms:
        if val<=v: best=(val,nm)
        else: break
    return best
def nexxt(v):
    for val,nm in syms:
        if val>v: return val
    return v+0x400
tgt=0x6afbe
sv,sn = enclosing(tgt)
print("目标 0x%x 所在符号: %s @0x%x" % (tgt, sn, sv))
end = nexxt(sv)
if end-sv > 0x800: end = sv+0x800
print("反汇编 0x%x .. 0x%x" % (sv, end))
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
o=rva2off(sv); code=d[o:o+(end-sv)]
for ins in md.disasm(code, sv):
    mk = "   <<<<< xref" if ins.address<=tgt<ins.address+ins.size else ""
    print("  0x%06x  %-20s %s %s%s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, mk))
