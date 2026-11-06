
import struct, sys
p = r'D:\software\dobot\V1.3.4-stable\RobotMaintenanceTools.exe'
d = open(p,'rb').read()
print("size", len(d))
if d[:2] != b'MZ': print("not MZ"); sys.exit()
e_lfanew = struct.unpack_from('<I', d, 0x3c)[0]
print("e_lfanew", hex(e_lfanew), d[e_lfanew:e_lfanew+4])
assert d[e_lfanew:e_lfanew+4] == b'PE\x00\x00'
coff = e_lfanew + 4
machine, nsec, timestamp, psym, nsym, optsize, chars = struct.unpack_from('<HHIIIHH', d, coff)
print("machine=0x%04x  sections=%d  ptrSymTab=0x%x  numSym=%d  optHdrSize=%d  chars=0x%04x" % (machine, nsec, psym, nsym, optsize, chars))
if psym and nsym:
    # string table right after symbol table
    st = psym + nsym*18
    stsize = struct.unpack_from('<I', d, st)[0]
    print("COFF string table size", stsize)
    def getname(off8):
        # symbol name: 8 bytes (inline or offset into string table)
        if off8[:4] == b'\x00\x00\x00\x00':
            o = struct.unpack_from('<I', off8, 4)[0]
            e = d.index(b'\x00', st+o)
            return d[st+o:e].decode('latin-1')
        return off8.rstrip(b'\x00').decode('latin-1')
    hits=[]
    for i in range(nsym):
        off = psym + i*18
        nm = getname(d[off:off+8])
        val, sec, typ, cls, naux = struct.unpack_from('<IhHBB', d, off+8)
        if any(k in nm for k in ('Password','password','getRandom','Random','Servo','servo')):
            hits.append((nm, val, sec))
    print("匹配符号 %d 个:" % len(hits))
    for nm,val,sec in hits[:60]:
        print("   sec=%d  val=0x%08x  %s" % (sec, val, nm))
else:
    print("无 COFF 符号表")
