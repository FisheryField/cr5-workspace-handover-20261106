
import struct
p = r'D:\software\dobot\V1.3.4-stable\RobotMaintenanceTools.exe'
d=open(p,'rb').read()
e=struct.unpack_from('<I',d,0x3c)[0]; coff=e+4
machine,nsec,ts,psym,nsym,optsize,chars=struct.unpack_from('<HHIIIHH',d,coff)
opt=coff+20; imgbase=struct.unpack_from('<I',d,opt+28)[0]
ndd = struct.unpack_from('<I', d, opt+92)[0]
print("数据目录数 =", ndd)
dirs=[]
for i in range(ndd):
    addr,size = struct.unpack_from('<II', d, opt+96+i*8)
    dirs.append((i,addr,size))
for i,a,s in dirs:
    if s: print("  dir[%d] rva=0x%x size=0x%x" % (i,a,s))
sectab=opt+optsize
secs=[]
for i in range(nsec):
    off=sectab+i*40
    name=d[off:off+8].rstrip(b'\x00').decode('latin-1')
    vsize,va,rawsize,rawptr=struct.unpack_from('<IIII',d,off+8)
    secs.append((name,va,vsize,rawptr,rawsize))
def rva2off(rva):
    for name,va,vsize,rawptr,rawsize in secs:
        if va<=rva<va+max(vsize,rawsize): return rawptr+(rva-va),name
    return None,None
# 重定位表 = dir[5]
rel_rva, rel_size = 0,0
for i,a,s in dirs:
    if i==5: rel_rva, rel_size = a,s
print("reloc rva=0x%x size=0x%x" % (rel_rva, rel_size))
o,_ = rva2off(rel_rva)
# 有的节可能没在节表里（如 /41 等），直接用 rva2off+raw
offs=[]
pos=o; end=o+rel_size
while pos < end:
    page, blk = struct.unpack_from('<II', d, pos); pos+=8
    n = (blk-8)//2
    if page==0 and blk==0: break
    for k in range(n):
        w = struct.unpack_from('<H', d, pos)[0]; pos+=2
        if w>>12 == 3:  # IMAGE_REL_BASED_HIGHLOW
            offs.append(page + (w & 0xFFF))
print("重定位项数 =", len(offs))
# 目标
targets = {0x5af5d0:'_g_strServoParamsPassword', 0x54cacc:'"Random code: %1"', 0x5534f9:'请输入：', 0x553168:'Mac'}
hits={k:[] for k in targets}
for rva in offs:
    o2,_=rva2off(rva)
    if o2 is None or o2+4>len(d): continue
    v = struct.unpack_from('<I', d, o2)[0]
    if v in targets: hits[v].append(rva)
for v,name in targets.items():
    print("%-28s 0x%08x : %d 处引用 -> %s" % (name, v, len(hits[v]), [hex(x) for x in hits[v][:12]]))
