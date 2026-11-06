import sys
sys.path.insert(0, r"D:\mydata\workspace\.pylibs")
sys.path.insert(0, r"D:\mydata\workspace\tools")
import struct, re
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
from libdata_strrefs import Elf
e = Elf()
d = e.d
def cstr_at(va):
    fo, sec = e.fileoff(va)
    if fo is None: return None
    end = d.find(b"\0", fo, fo+140)
    if end < 0: return None
    try: s = d[fo:end].decode("ascii")
    except: return None
    if len(s) >= 2 and all(32 <= ord(c) < 127 for c in s): return s
    return None
for pool_va in (0x11b530, 0x11b52c, 0x11b4fc, 0x11b4f8, 0x11b1c4):
    fo,_ = e.fileoff(pool_va)
    w = struct.unpack_from("<I", d, fo)[0]
    # these are used as: ldr r1,[pc]; add r1,pc  (insn at pool_va-8 roughly) -> tgt = insn+4+w, unknown insn addr; try both insn addr guesses
    print(hex(pool_va), "w=0x%08x" % w)
