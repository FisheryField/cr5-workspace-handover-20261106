import sys, struct
sys.path.insert(0, '.pylibs')
import capstone

SO = 'libdataSvr.so.bin'
data = open(SO, 'rb').read()
assert data[:4] == b'\x7fELF'
e_phoff = struct.unpack_from('<I', data, 0x1c)[0]
e_phentsize, e_phnum = struct.unpack_from('<HH', data, 0x2a)
segs = []
for i in range(e_phnum):
    off = e_phoff + i * e_phentsize
    p_type, p_offset, p_vaddr, _, p_filesz = struct.unpack_from('<IIIII', data, off)
    if p_type == 1:
        segs.append((p_vaddr, p_offset, p_filesz))

def v2o(v):
    for va, off, sz in segs:
        if va <= v < va + sz:
            return off + (v - va)
    return None

def rd_cstr(v, maxlen=80):
    o = v2o(v)
    if o is None:
        return None
    end = data.find(b'\0', o, o + maxlen)
    if end < 0:
        return None
    s = data[o:end]
    if not all(32 <= c < 127 for c in s):
        return None
    return s.decode()

md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.detail = True
LO, HI = 0x11a1c0, 0x11b900
o = v2o(LO)
code = data[o:o + (HI - LO)]

insns = list(md.disasm(code, LO))
# map: track pending ldr rX,[pc,#imm] literal value per register, resolve on 'add rX, pc'
pend = {}
for idx, insn in enumerate(insns):
    if insn.mnemonic.startswith('ldr') and '[pc' in insn.op_str and ',' in insn.op_str:
        try:
            reg = insn.op_str.split(',')[0].strip()
            imm = int(insn.op_str.split('#')[-1].rstrip(']'), 0)
            pc = (insn.address + 4) & ~3
            lo_ = v2o(pc + imm)
            if lo_ is not None:
                pend[reg] = struct.unpack_from('<I', data, lo_)[0]
        except Exception:
            pass
    elif insn.mnemonic == 'add' and insn.op_str.endswith(', pc'):
        reg = insn.op_str.split(',')[0].strip()
        if reg in pend:
            final = pend[reg] + insn.address + 4
            s = rd_cstr(final)
            if s:
                print('%08x  ADD-PC %-6s -> 0x%08x  "%s"' % (insn.address, reg, final, s))
            else:
                print('%08x  ADD-PC %-6s -> 0x%08x  (non-str)' % (insn.address, reg, final))
            del pend[reg]
    elif insn.mnemonic.startswith('ldr') and ',' in insn.op_str and insn.op_str.split(',')[0].strip() in pend:
        # register reused by another load - drop
        reg = insn.op_str.split(',')[0].strip()
        if reg in pend and ('[pc' not in insn.op_str):
            del pend[reg]
