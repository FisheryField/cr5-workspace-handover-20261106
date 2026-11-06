import sys
sys.path.insert(0, r"D:\mydata\workspace\.pylibs")
sys.path.insert(0, r"D:\mydata\workspace\tools")
import struct, re
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
from libdata_strrefs import Elf
e = Elf()
d = e.d
cs = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
def cstr_at(va):
    fo, sec = e.fileoff(va)
    if fo is None: return None
    end = d.find(b"\0", fo, fo+120)
    if end < 0: return None
    try: s = d[fo:end].decode("ascii")
    except: return None
    if len(s) >= 2 and all(32 <= ord(c) < 127 for c in s): return s
    return None
# scan whole protoExchange function region 0x11a200..0x11a8c0 for pic string refs
start_va, end_va = 0x11a200, 0x11a8c0
fo, _ = e.fileoff(start_va)
code = d[fo:fo+(end_va-start_va)]
seq = list(cs.disasm(code, start_va))
for i, insn in enumerate(seq):
    if insn.mnemonic.startswith("ldr") and "pc" in insn.op_str:
        m = re.search(r"pc,\s*#(0x[0-9a-f]+|\d+)", insn.op_str)
        if not m: continue
        imm = int(m.group(1), 0)
        pool_va = ((insn.address+4)&~3) + imm
        fo2, sec = e.fileoff(pool_va)
        if fo2 is None: continue
        w = struct.unpack_from("<I", d, fo2)[0]
        for j in range(i+1, min(i+4, len(seq))):
            nj = seq[j]
            if nj.mnemonic in ("add","addw") and nj.op_str.endswith("pc"):
                tgt = nj.address + 4 + w if nj.mnemonic=="add" else None
                if tgt is None: continue
                s = cstr_at(tgt)
                if s: print("0x%08x -> %r" % (insn.address, s))
                break
