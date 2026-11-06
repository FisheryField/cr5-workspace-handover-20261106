
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
def off2rva(o):
    for name,va,vsize,rawptr,rawsize in secs:
        if rawptr<=o<rawptr+rawsize: return va+(o-rawptr), name
    return None,None
def rva2off(rva):
    for name,va,vsize,rawptr,rawsize in secs:
        if va<=rva<va+max(vsize,rawsize): return rawptr+(rva-va)
    return None
# 找字符串
targets = {}
for s in (b'Random code:', b'servoParamsPassword', b'servoParamPassword'):
    i = d.find(s)
    if i>=0:
        rva,sec = off2rva(i)
        targets[s] = rva
        print("%-22r file@0x%x  rva=0x%x  sec=%s" % (s, i, rva, sec))
print()
T=secs[0]; tva,tvsize,traw=T[1],T[2],T[3]
text=d[traw:traw+tvsize]
for s,rva in targets.items():
    pat=struct.pack('<I', imgbase+rva)
    hits=[]; i=0
    while True:
        j=text.find(pat,i)
        if j<0: break
        hits.append(tva+j); i=j+1
    print("%r -> %d xrefs: %s" % (s, len(hits), [hex(x) for x in hits[:10]]))
# 也试试 lea 用的偏移（有些是 [reg+disp]），先看直接引用
