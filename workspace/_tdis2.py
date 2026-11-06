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
    if va is None: return None
    fo, sec = e.fileoff(va)
    if fo is None: return None
    end = d.find(b"\0", fo, fo+200)
    if end < 0: return None
    try: s = d[fo:end].decode("ascii")
    except: return None
    if len(s) >= 3 and all(32 <= ord(c) < 127 for c in s): return s
    return None

start_va = 0x11a860
fo, _ = e.fileoff(start_va)
code = d[fo:fo+0x2e0]
# collect pc-relative literal loads: ldr rX,[pc,#imm] -> pool addr
pool = {}
for insn in cs.disasm(code, start_va):
    line = "0x%08x  %-8s %s" % (insn.address, insn.mnemonic, insn.op_str)
    ann = ""
    if insn.mnemonic.startswith("ldr") and "pc" in insn.op_str:
        # compute pool address (Thumb: align(pc,4)+imm)
        import re as _re
        m = _re.search(r"pc,\s*#(0x[0-9a-f]+|\d+)", insn.op_str)
        if m:
            imm = int(m.group(1), 0)
            base = (insn.address + 4) & ~3
            pool_va = base + imm
            fo2, sec = e.fileoff(pool_va)
            if fo2 is not None:
                w = struct.unpack_from("<I", d, fo2)[0]
                # PIC: value is offset added to pc later; try both raw string and offset
                ann = " ; pool[0x%x]=0x%x" % (pool_va, w)
                s = cstr_at(w)
                if s: ann += " str=%r" % s
                # pic: pc + w
                tgt = insn.address + 4 + w  # approximate if next insn is add rX,pc
                s2 = cstr_at(tgt)
                if s2: ann += " pic->%r" % s2
    print(line + ann)
