
import struct, sys, capstone
p = r'D:\software\dobot\V1.3.4-stable\RobotMaintenanceTools.exe'
d = open(p,'rb').read()
e = struct.unpack_from('<I', d, 0x3c)[0]; coff = e+4
machine, nsec, ts, psym, nsym, optsize, chars = struct.unpack_from('<HHIIIHH', d, coff)
opt = coff+20; sectab = opt+optsize
secs=[]
for i in range(nsec):
    off = sectab + i*40
    name = d[off:off+8].rstrip(b'\x00').decode('latin-1')
    vsize, va, rawsize, rawptr = struct.unpack_from('<IIII', d, off+8)
    secs.append((name, va, vsize, rawptr, rawsize))
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
def va2off(sec,val):
    name, va, vsize, rawptr, rawsize = secs[sec-1]
    return rawptr + (val-va)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def dis(sec, val, label):
    end = nextsym(sec,val)
    if end is None or end-val > 0x2000: end = val+0x300
    off = va2off(sec,val)
    code = d[off:off+(end-val)]
    print("="*78)
    print("%s   VA=0x%x  off=0x%x  size=%d" % (label, val, off, len(code)))
    print("="*78)
    for ins in md.disasm(code, val):
        line = "  0x%06x  %-24s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str)
        print(line)
# WidgetServoParamsPassword::getRandom
dis(1, 0x946f0, "WidgetServoParamsPassword::getRandom()")
# initStatus
dis(1, 0x94740, "WidgetServoParamsPassword::initStatus()")
