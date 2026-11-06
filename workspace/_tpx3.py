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
    end = d.find(b"\0", fo, fo+140)
    if end < 0: return None
    try: s = d[fo:end].decode("ascii")
    except: return None
    if len(s) >= 2 and all(32 <= ord(c) < 127 for c in s): return s
    return None
start_va = 0x11a200
fo, _ = e.fileoff(start_va)
code = d[fo:fo+0x130]
seq = list(cs.disasm(code, start_va))
for i, insn in enumerate(seq):
    line = "0x%08x  %-8s %s" % (insn.address, insn.mnemonic, insn.op_str)
    ann = ""
    if insn.mnemonic.startswith("ldr") and "pc" in insn.op_str:
        m = re.search(r"pc,\s*#(0x[0-9a-f]+|\d+)", insn.op_str)
        if m:
            imm = int(m.group(1), 0)
            pool_va = ((insn.address+4)&~3) + imm
            fo2, sec = e.fileoff(pool_va)
            if fo2 is not None:
                w = struct.unpack_from("<I", d, fo2)[0]
                ann = " ; pool=0x%x" % w
                for j in range(i+1, min(i+4, len(seq))):
                    nj = seq[j]
                    if nj.mnemonic == "add" and nj.op_str.endswith(", pc"):
                        s = cstr_at(nj.address + 4 + w)
                        if s: ann += " pic->%r" % s
                        break
    print(line + ann)
