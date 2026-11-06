
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
    if 1<=sec<=nsec: syms.append((sec,secs[sec-1][1]+val,val,nm))
t1=sorted(set((r,n) for s,r,v,n in syms if s==1))
# 找 MainWidget2::event 的起点
start=None
for r,n in t1:
    if n=='__ZN11MainWidget25eventEP6QEvent': start=r
print("MainWidget2::event RVA = 0x%x" % start)
# 从 start 反汇编到 xref 之后
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
o=rva2off(start); code=d[o:o+(0x6b0c0-start)]
cnt=0
for ins in md.disasm(code, start):
    cnt+=1
    if 0x6aefa <= ins.address <= 0x6b0c0:
        mk=""
        if ins.address==0x6afba: mk="   <<<< Random code"
        print("  0x%06x  %-18s %s %s%s" % (ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str,mk))
print("total insns", cnt)
