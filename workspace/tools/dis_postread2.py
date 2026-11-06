
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
def cstr(rva, n=60):
    o=rva2off(rva)
    if o is None: return None
    en=d.index(b'\x00',o,o+n); raw=d[o:en]
    return raw.decode('utf-8','replace') if raw else None
print("=== 0x54e5e0..0x54e660 的串 ===")
o=rva2off(0x14e5e0); blob=d[o:o+0x80]
cur=b''; base=0x14e5e0; i=0
while i<len(blob):
    c=blob[i]
    if 32<=c<127:
        if not cur: base=0x14e5e0+i
        cur+=bytes([c])
    else:
        if len(cur)>=2: print("  0x%06x(abs 0x%08x): %r" % (base,0x400000+base,cur.decode('latin-1')))
        cur=b''
    i+=1
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
o=rva2off(0x7ae95); code=d[o:o+0x1c0]
print()
print("=== postSettingsReadServoParams 循环体 0x7ae95..0x7b055 ===")
for ins in md.disasm(code, 0x7ae95):
    note=""
    for m in re.finditer(r'0x(5[0-9a-f]{5})', ins.op_str):
        v=int(m.group(1),16)
        if 0x540000<=v<=0x560000:
            s=cstr(v-0x400000,60)
            if s: note='   ; "%s"' % s
    print("  0x%06x  %-16s %-32s%s" % (ins.address, ins.bytes.hex(), ins.mnemonic+' '+ins.op_str, note))
