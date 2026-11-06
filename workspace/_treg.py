import sys
sys.path.insert(0, r"D:\mydata\workspace\.pylibs")
sys.path.insert(0, r"D:\mydata\workspace\tools")
import struct, re
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
from libdata_strrefs import Elf
e = Elf()
d = e.d
cs = Cs(CS_ARCH_ARM, CS_MODE_THUMB)

def cstr_at(va, maxlen=100):
    fo, sec = e.fileoff(va)
    if fo is None: return None
    end = d.find(b"\0", fo, fo+maxlen)
    if end < 0: return None
    try: s = d[fo:end].decode("ascii")
    except: return None
    if len(s) >= 2 and all(32 <= ord(c) < 127 for c in s): return s
    return None

# scan the ctor region 0x10b3f0..0x10e3f0 (12096 B) for the idiom:
#   ldr.w r0,[pc,#imm] ; add r0,pc   -> QString of route token
# record (insn_addr, resolved_string)
start_va, end_va = 0x10b3f0, 0x10e3f0
fo, _ = e.fileoff(start_va)
code = d[fo:fo+(end_va-start_va)]
seq = list(cs.disasm(code, start_va))
resolved = []
for i, insn in enumerate(seq):
    if insn.mnemonic.startswith("ldr") and "pc" in insn.op_str:
        m = re.search(r"pc,\s*#(0x[0-9a-f]+|\d+)", insn.op_str)
        if not m: continue
        imm = int(m.group(1), 0)
        base = (insn.address + 4) & ~3
        pool_va = base + imm
        fo2, sec = e.fileoff(pool_va)
        if fo2 is None: continue
        w = struct.unpack_from("<I", d, fo2)[0]
        # next: add rX, pc within 3 insns
        for j in range(i+1, min(i+4, len(seq))):
            nj = seq[j]
            if nj.mnemonic == "add" and nj.op_str.endswith(", pc"):
                tgt = insn.address + 4 + w  # pic approximation (actual: nj addr)
                # more accurate: tgt = nj.address + 4 + w  for Thumb add rX,pc
                tgt2 = nj.address + 4 + w
                s = cstr_at(tgt2)
                if s:
                    resolved.append((insn.address, s))
                break
print("resolved route-ish strings: %d" % len(resolved))
for a, s in resolved:
    if any(k in s.lower() for k in ("clear", "alarm", "exchange", "proto", "calib", "home", "controlmode")):
        print("0x%08x  %r" % (a, s))
