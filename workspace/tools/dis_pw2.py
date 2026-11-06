
import struct, sys, capstone
p = r'D:\software\dobot\V1.3.4-stable\RobotMaintenanceTools.exe'
d = open(p,'rb').read()
e = struct.unpack_from('<I', d, 0x3c)[0]; coff=e+4
machine,nsec,ts,psym,nsym,optsize,chars = struct.unpack_from('<HHIIIHH', d, coff)
opt = coff+20
magic = struct.unpack_from('<H', d, opt)[0]
imgbase = struct.unpack_from('<I', d, opt+28)[0]
print("magic=0x%04x  ImageBase=0x%x" % (magic, imgbase))
sectab = opt+optsize
secs=[]
for i in range(nsec):
    off=sectab+i*40
    name=d[off:off+8].rstrip(b'\x00').decode('latin-1')
    vsize,va,rawsize,rawptr = struct.unpack_from('<IIII', d, off+8)
    secs.append((name,va,vsize,rawptr,rawsize))
def rva2off(rva):
    for name,va,vsize,rawptr,rawsize in secs:
        if va <= rva < va+max(vsize,rawsize): return rawptr+(rva-va)
    return None
def rdstr(rva, maxlen=64):
    o = rva2off(rva)
    if o is None: return None
    end = d.index(b'\x00', o, o+maxlen)
    return d[o:end]
for rva,n,label in [(0x153168,3,'initStatus str1'),(0x15316c,24,'initStatus str2')]:
    print("%s @rva 0x%x len=%d : %r" % (label, rva, n, rdstr(rva, n+8)))
print()
# .text 范围
T = secs[0]
tva, tvsize, traw = T[1], T[2], T[3]
text = d[traw:traw+tvsize]
# 找对 _g_strServoParamsPassword (rva 0x1af5d0) 的引用
target = imgbase + 0x1af5d0
pat = struct.pack('<I', target)
print("搜索 .text 中对 0x%08x (_g_strServoParamsPassword) 的引用:" % target)
idx=0; found=[]
while True:
    j = text.find(pat, idx)
    if j<0: break
    found.append(tva+j); idx=j+1
print("  命中 %d 处: %s" % (len(found), [hex(x) for x in found[:20]]))
# 反汇编 event()
st = psym + nsym*18
def getname(o8):
    if o8[:4]==b'\x00\x00\x00\x00':
        o=struct.unpack_from('<I',o8,4)[0]; en=d.index(b'\x00', st+o); return d[st+o:en].decode('latin-1')
    return o8.rstrip(b'\x00').decode('latin-1')
syms=[]
for i in range(nsym):
    off=psym+i*18; nm=getname(d[off:off+8]); val,sec,typ,cls,naux=struct.unpack_from('<IhHBB',d,off+8)
    if sec>0: syms.append((sec,val,nm))
syms.sort()
def nextsym(sec,val):
    for s,v,n in syms:
        if s==sec and v>val: return v
    return None
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def dis(sec,val,label,limit=0x400):
    end = nextsym(sec,val); 
    if end is None or end-val>limit: end=val+limit
    o = rva2off(val)
    code = d[o:o+(end-val)]
    print("="*76); print("%s  RVA=0x%x size=%d" % (label,val,len(code))); print("="*76)
    for ins in md.disasm(code,val):
        s="  0x%06x  %-22s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str)
        print(s)
dis(1, 0x4b80, "CommonData::getRandom()", 0x200)
