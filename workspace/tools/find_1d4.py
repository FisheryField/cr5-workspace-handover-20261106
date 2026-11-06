
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
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
hits=[]
for i,(rva,nm) in enumerate(t1):
    if not (nm.startswith('__ZN11MainWidget2') or True): continue
    nxt = t1[i+1][0] if i+1<len(t1) else rva+0x400
    if nxt<=rva: continue
    o=rva2off(rva)
    if o is None: continue
    code=d[o:o+min(nxt-rva,0x4000)]
    for ins in md.disasm(code, rva):
        if '0x1d4' in ins.op_str:
            hits.append((ins.address, nm, ins.mnemonic+' '+ins.op_str))
print("引用 +0x1d4 的指令 %d 条:" % len(hits))
for a,nm,txt in hits[:40]:
    print("   0x%06x  %-52s %s" % (a, nm[:50], txt))
print()
# 再找 MainWidget2::event 中所有 call 到 libdataSvr/http 相关？先看 event 尾部
print("=== MainWidget2::event 尾部 (0x6b0c0..0x6b3a0) ===")
o=rva2off(0x6b0c0); code=d[o:o+0x2e0]
for ins in md.disasm(code, 0x6b0c0):
    print("  0x%06x  %-18s %s %s" % (ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))
