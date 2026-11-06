import sys
sys.path.insert(0, r"D:\mydata\workspace\.pylibs")
sys.path.insert(0, r"D:\mydata\workspace\tools")
import struct
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
import re as _re
for anchor, span in ((0x10c4d8, 0x40), (0x10c892, 0x60)):
    print("=== around 0x%x" % anchor)
    fo, _ = e.fileoff(anchor - 0x20)
    code = d[fo:fo+span+0x40]
    for insn in cs.disasm(code, anchor-0x20):
        line = "0x%08x  %-8s %s" % (insn.address, insn.mnemonic, insn.op_str)
        ann = ""
        if insn.mnemonic.startswith("ldr") and "pc" in insn.op_str:
            m = _re.search(r"pc,\s*#(0x[0-9a-f]+|\d+)", insn.op_str)
            if m:
                imm = int(m.group(1), 0)
                base = (insn.address + 4) & ~3
                pool_va = base + imm
                fo2, sec = e.fileoff(pool_va)
                if fo2 is not None:
                    w = struct.unpack_from("<I", d, fo2)[0]
                    ann = " ; pool=0x%x" % w
                    s = cstr_at(insn.address + 4 + w)
                    if s: ann += " pic->%r" % s
        print(line + ann)
