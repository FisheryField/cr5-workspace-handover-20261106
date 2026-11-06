
import struct, capstone
p = r'D:\mydata\workspace\libdataSvr.so.bin'
d=open(p,'rb').read()
endian='<'
e_shoff=struct.unpack_from('<I',d,0x20)[0]
e_shentsize=struct.unpack_from('<H',d,0x2e)[0]
e_shnum=struct.unpack_from('<H',d,0x30)[0]
e_shstrndx=struct.unpack_from('<H',d,0x32)[0]
secs=[]
for i in range(e_shnum):
    o=e_shoff+i*e_shentsize
    name,typ,flags,addr,off,size,link,info,align,entsize=struct.unpack_from('<IIIIIIIIII',d,o)
    secs.append(dict(name=name,type=typ,flags=flags,addr=addr,off=off,size=size,entsize=entsize))
shstr=secs[e_shstrndx]
def sname(n):
    o=shstr['off']+n; e=d.index(b'\x00',o); return d[o:e].decode('latin-1')
for s in secs: s['sname']=sname(s['name'])
def va2off(va):
    for s in secs:
        if s['type']!=8 and s['addr']<=va<s['addr']+s['size']:
            return s['off']+(va-s['addr'])
    return None
def cstr(va, n=80):
    o=va2off(va)
    if o is None: return None
    e=d.index(b'\x00',o,o+n)
    return d[o:e]
# 反汇编 parseAndReqGetServoParams (Thumb)
START=0xec03d; SIZE=1080
o=va2off(START)
md=capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.detail=True
pool={}
print("=== parseAndReqGetServoParams @0x%x (%d B) ===" % (START,SIZE))
for ins in md.disasm(d[o:o+SIZE], START):
    line="  0x%06x  %-10s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str)
    extra=""
    # 解析 PC 相对 ldr 取字面量
    if ins.mnemonic.startswith('ldr') and 'pc' in ins.op_str:
        try:
            imm = ins.operands[1].mem.disp
            base = (ins.address + 4) & ~3
            litva = base + imm
            lo = va2off(litva)
            if lo is not None:
                val = struct.unpack_from('<I', d, lo)[0]
                s = cstr(val, 60)
                pool[ins.operands[0].reg] = val
                if s and all(32<=c<127 or c>=0x80 for c in s):
                    extra = '   ; -> 0x%x  "%s"' % (val, s.decode('utf-8','replace'))
                else:
                    extra = '   ; -> 0x%x' % val
        except Exception:
            pass
    print(line+extra)
