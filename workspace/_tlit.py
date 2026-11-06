import sys
sys.path.insert(0, r"D:\mydata\workspace\.pylibs")
sys.path.insert(0, r"D:\mydata\workspace\tools")
import struct
from libdata_strrefs import Elf
e = Elf()
d = e.d
def cstr_at(va):
    fo, sec = e.fileoff(va)
    if fo is None: return None
    end = d.find(b"\0", fo, fo+120)
    if end < 0: return None
    try: s = d[fo:end].decode("ascii")
    except: return None
    if len(s) >= 2 and all(32 <= ord(c) < 127 for c in s): return s
    return None
# construction block insns: 0x11a6fc..0x11a836, each: ldr r1,[pc,#imm]; add r1,pc
# pool addrs computed per insn
for insn_va in (0x11a70c, 0x11a724, 0x11a73c, 0x11a754, 0x11a76c, 0x11a784, 0x11a79c, 0x11a7b4, 0x11a7cc, 0x11a7e4, 0x11a7fc, 0x11a814, 0x11a82c):
    imm = {0x11a70c:0xa80,0x11a724:0xa6c,0x11a73c:0xa58,0x11a754:0xa44,0x11a76c:0xa30,
           0x11a784:0xa1c,0x11a79c:0xa08,0x11a7b4:0x9f4,0x11a7cc:0x9e0,0x11a7e4:0x9cc,
           0x11a7fc:0x9b8,0x11a814:0x9a4,0x11a82c:0x990}[insn_va]
    pool_va = ((insn_va+4)&~3) + imm
    fo,_ = e.fileoff(pool_va)
    w = struct.unpack_from("<I", d, fo)[0]
    # add r1,pc follows at insn_va+6; target = (insn_va+6)+4+w
    tgt = insn_va + 6 + 4 + w
    print("insn 0x%x pool[0x%x]=0x%08x -> %r" % (insn_va, pool_va, w, cstr_at(tgt)))
