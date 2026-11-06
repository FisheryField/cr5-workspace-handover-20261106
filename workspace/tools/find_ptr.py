
import struct, sys
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
def off2sec(o):
    for name,va,vsize,rawptr,rawsize in secs:
        if rawptr<=o<rawptr+rawsize: return name, va+(o-rawptr)
    return None,None
for target,label in ((0x47ad40,'postSettingsReadServoParams'),(0x47b560,'postSettingsModifyServoParams')):
    pat=struct.pack('<I',target)
    hits=[]; i=0
    while True:
        j=d.find(pat,i)
        if j<0: break
        nm,rva=off2sec(j)
        hits.append((j,rva,nm))
        i=j+1
    print("=== %s (0x%x) : %d 处 ===" % (label,target,len(hits)))
    for o,rva,nm in hits[:12]:
        print("   file@0x%08x  rva=0x%08x  sec=%s" % (o, rva or 0, nm))
    print()
