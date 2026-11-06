
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
        if va<=rva<va+max(vsize,rawsize): return rawptr+(rva-va)
    return None
# dump 字符串区 0x14e580..0x14e6c0
start=0x14e580; o=rva2off(start)
blob=d[o:o+0x180]
print("RVA 0x%x 起 %d 字节的可打印串：" % (start, len(blob)))
cur=b''; base=start
i=0
while i < len(blob):
    c=blob[i]
    if 32<=c<127:
        if not cur: base=start+i
        cur+=bytes([c])
    else:
        if len(cur)>=2:
            print("   rva 0x%06x  (abs 0x%08x) : %r" % (base, 0x400000+base, cur.decode('latin-1')))
        cur=b''
    i+=1
if len(cur)>=2: print("   rva 0x%06x : %r" % (base, cur.decode('latin-1')))
# 也找 JSON 模板特征串
import re
for pat in (b'{"key"', b'"key"', b'"value"', b'{"data"', b'"status"', b'"params"', b'"slave"', b'"index"'):
    idxs=[m.start() for m in re.finditer(re.escape(pat), d)][:6]
    print("%-12r : %s" % (pat, [(hex(x), hex(0x400000+ (rva2off and 0))) for x in idxs[:3]]))
