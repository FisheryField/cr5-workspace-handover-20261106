
import struct, sys, capstone
p = r'D:\software\dobot\V1.3.4-stable\RobotMaintenanceTools.exe'
d = open(p,'rb').read()
e = struct.unpack_from('<I', d, 0x3c)[0]; coff=e+4
machine,nsec,ts,psym,nsym,optsize,chars = struct.unpack_from('<HHIIIHH', d, coff)
opt=coff+20; imgbase=struct.unpack_from('<I', d, opt+28)[0]
sectab=opt+optsize
secs=[]
for i in range(nsec):
    off=sectab+i*40
    name=d[off:off+8].rstrip(b'\x00').decode('latin-1')
    vsize,va,rawsize,rawptr=struct.unpack_from('<IIII', d, off+8)
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
    if sec>0: syms.append((sec,val,nm))
syms.sort()
def enclosing(sec,val):
    best=None
    for s,v,n in syms:
        if s==sec and v<=val: best=(s,v,n)
        elif s==sec and v>val: break
    return best
def nextsym(sec,val):
    for s,v,n in syms:
        if s==sec and v>val: return v
    return None
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail=False
def dis_range(sec,start,end,label,tag=()):
    o=rva2off(start); code=d[o:o+(end-start)]
    print("="*76); print("%s   RVA 0x%x..0x%x  (%d bytes)" % (label,start,end,end-start)); print("="*76)
    for ins in md.disasm(code,start):
        mark = " <<<" if ins.address in tag else ""
        print("  0x%06x  %-20s %s %s%s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, mark))
for addr in (0x74c1, 0x12a944):
    s,v,n = enclosing(1, addr)
    e2 = nextsym(1, v) or v+0x200
    if e2-v > 0x600: e2 = v+0x600
    dis_range(1, v, e2, "包含 0x%x 的函数 [%s]" % (addr, n), tag=(addr,))
