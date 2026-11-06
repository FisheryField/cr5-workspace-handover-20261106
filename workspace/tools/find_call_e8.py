
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
st=psym+nsym*18
def getname(o8):
    if o8[:4]==b'\x00\x00\x00\x00':
        o=struct.unpack_from('<I',o8,4)[0]; en=d.index(b'\x00',st+o); return d[st+o:en].decode('latin-1')
    return o8.rstrip(b'\x00').decode('latin-1')
t1=[]
for i in range(nsym):
    off=psym+i*18; nm=getname(d[off:off+8]); val,sec,typ,cls,naux=struct.unpack_from('<IhHBB',d,off+8)
    if sec==1: t1.append((secs[0][1]+val, nm))
t1.sort()
def sym_at(rva):
    best=None
    for r,n in t1:
        if r<=rva: best=(r,n)
        else: break
    return best
T=sectab  # .text section index 0
tn,tva,tvsz,traw,trsz = secs[0]
text=d[traw:traw+trsz]
TARGETS={0x7ad40:'postSettingsReadServoParams', 0x7b560:'postSettingsModifyServoParams'}
res={k:[] for k in TARGETS}
for i in range(len(text)-5):
    if text[i]!=0xE8: continue
    disp=struct.unpack_from('<i', text, i+1)[0]
    ins_rva = tva + i
    tgt = ins_rva + 5 + disp
    if tgt in TARGETS:
        res[tgt].append(ins_rva)
for k,name in TARGETS.items():
    print("=== call %s (0x%x) : %d 处 ===" % (name,k,len(res[k])))
    for a in res[k][:10]:
        sa=sym_at(a)
        print("   0x%06x  in  %s" % (a, sa[1][:100] if sa else '?'))
