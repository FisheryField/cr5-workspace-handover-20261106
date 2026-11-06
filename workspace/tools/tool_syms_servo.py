
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
st=psym+nsym*18
def getname(o8):
    if o8[:4]==b'\x00\x00\x00\x00':
        o=struct.unpack_from('<I',o8,4)[0]; en=d.index(b'\x00',st+o); return d[st+o:en].decode('latin-1')
    return o8.rstrip(b'\x00').decode('latin-1')
rows=[]
for i in range(nsym):
    off=psym+i*18; nm=getname(d[off:off+8]); val,sec,typ,cls,naux=struct.unpack_from('<IhHBB',d,off+8)
    if 1<=sec<=nsec: rows.append((sec,secs[sec-1][1]+val,val,nm))
import re
print("=== 含 StructSettingsServoParam / SettingsServoParams 的符号 ===")
for sec,rva,val,nm in sorted(rows):
    if 'StructSettingsServoParam' in nm or 'SettingsServoParams' in nm:
        print("  sec=%d RVA=0x%08x (val=0x%x)  %s" % (sec,rva,val,nm))
print()
print("=== dob_export / 其它相关 ===")
for sec,rva,val,nm in sorted(rows):
    if re.search(r'ServoParam', nm) and 'MainWidget2' in nm:
        print("  RVA=0x%08x  %s" % (rva,nm))
