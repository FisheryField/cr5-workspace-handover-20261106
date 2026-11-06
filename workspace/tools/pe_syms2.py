
import struct, sys
p = r'D:\software\dobot\V1.3.4-stable\RobotMaintenanceTools.exe'
d = open(p,'rb').read()
e = struct.unpack_from('<I', d, 0x3c)[0]
coff = e+4
machine, nsec, ts, psym, nsym, optsize, chars = struct.unpack_from('<HHIIIHH', d, coff)
opt = coff+20
# PE32 optional header: section table at opt+optsize
sectab = opt + optsize
secs=[]
for i in range(nsec):
    off = sectab + i*40
    name = d[off:off+8].rstrip(b'\x00').decode('latin-1')
    vsize, va, rawsize, rawptr = struct.unpack_from('<IIII', d, off+8)
    secs.append((name, va, vsize, rawptr, rawsize))
    print("sec%-2d %-9s VA=0x%08x vsize=0x%-7x raw@0x%08x size=0x%x" % (i+1, name, va, vsize, rawptr, rawsize))
def va2off(secidx, val):
    if secidx == 0: return None
    name, va, vsize, rawptr, rawsize = secs[secidx-1]
    return rawptr + (val - va)
st = psym + nsym*18
def getname(off8):
    if off8[:4] == b'\x00\x00\x00\x00':
        o = struct.unpack_from('<I', off8, 4)[0]
        en = d.index(b'\x00', st+o)
        return d[st+o:en].decode('latin-1')
    return off8.rstrip(b'\x00').decode('latin-1')
syms=[]
for i in range(nsym):
    off = psym + i*18
    nm = getname(d[off:off+8])
    val, sec, typ, cls, naux = struct.unpack_from('<IhHBB', d, off+8)
    syms.append((nm,val,sec,naux))
print()
print("=== 含 Password / Passwd 的符号 ===")
for nm,val,sec,naux in syms:
    if 'assword' in nm:
        print("   sec=%d 0x%08x  off=%s  %s" % (sec, val, va2off(sec,val), nm))
print()
print("=== 含 Random 的符号 ===")
for nm,val,sec,naux in syms:
    if 'Random' in nm or 'random' in nm.lower() and 'iterator' not in nm:
        print("   sec=%d 0x%08x  off=%s  %s" % (sec, val, va2off(sec,val), nm))
print()
print("=== MainWidget2 中与 ServoParam 相关的槽函数 ===")
for nm,val,sec,naux in syms:
    if 'MainWidget2' in nm and ('ServoParam' in nm or 'Password' in nm):
        print("   sec=%d 0x%08x  %s" % (sec, val, nm))
