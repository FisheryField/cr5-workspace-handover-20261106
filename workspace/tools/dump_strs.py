
import struct
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
        if va<=rva<va+max(vsize,rawsize): return rawptr+(rva-va), name
    return None,None
for absaddr in (0x5531ef,0x5534f4,0x5534f9,0x553506,0x55350d,0x553168,0x55316c,0x54234c,0x5534f0):
    rva = absaddr - 0x400000
    o,name = rva2off(rva)
    if o is None:
        print("0x%08x (rva 0x%x): 不在任何节" % (absaddr, rva)); continue
    raw = d[o:o+64]
    end = raw.find(b'\x00')
    s = raw[:end if end>=0 else 64]
    try: txt = s.decode('utf-8')
    except Exception: txt = repr(s)
    print("0x%08x (rva 0x%06x, %-7s): %r" % (absaddr, rva, name, txt))
