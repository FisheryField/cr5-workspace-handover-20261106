import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath('.')), '.pylibs'))
sys.path.insert(0, '.pylibs')
import capstone

SO = 'libdataSvr.so.bin'
data = open(SO, 'rb').read()

# quick: parse ELF program headers manually to map vaddr->off (32-bit ARM LE)
import struct
assert data[:4] == b'\x7fELF'
is64 = data[4] == 2
if is64:
    e_phoff = struct.unpack_from('<Q', data, 0x20)[0]
    e_phentsize, e_phnum = struct.unpack_from('<HH', data, 0x36)
else:
    e_phoff = struct.unpack_from('<I', data, 0x1c)[0]
    e_phentsize, e_phnum = struct.unpack_from('<HH', data, 0x2a)
segs = []
for i in range(e_phnum):
    off = e_phoff + i * e_phentsize
    if is64:
        p_type, p_flags = struct.unpack_from('<II', data, off)
        p_offset, p_vaddr, _, p_filesz = struct.unpack_from('<QQQQ', data, off + 8)
    else:
        p_type, p_offset, p_vaddr, _, p_filesz = struct.unpack_from('<IIIII', data, off)
    if p_type == 1:
        segs.append((p_vaddr, p_offset, p_filesz))

def v2o(v):
    for va, off, sz in segs:
        if va <= v < va + sz:
            return off + (v - va)
    return None

def rd_cstr(v, maxlen=64):
    o = v2o(v)
    if o is None:
        return None
    end = data.find(b'\0', o, o + maxlen)
    if end < 0:
        return None
    try:
        return data[o:end].decode('utf-8', 'replace')
    except Exception:
        return None

# disassemble protoExchange dispatch region and dump string refs + calls
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.detail = True
LO, HI = 0x11a1c0, 0x11a900   # protoExchange region per checkpoint
o = v2o(LO)
code = data[o:o + (HI - LO)]
lits = []
for insn in md.disasm(code, LO):
    t = '%08x  %-8s %s' % (insn.address, insn.mnemonic, insn.op_str)
    note = ''
    # literal pool loads: ldr rX, [pc, #imm]
    if insn.mnemonic == 'ldr' and '[pc' in insn.op_str:
        try:
            imm = int(insn.op_str.split('#')[-1].rstrip(']'), 0)
            pc = (insn.address + 4) & ~3
            lit_va = pc + imm
            lo_ = v2o(lit_va)
            if lo_ is not None:
                val = struct.unpack_from('<I', data, lo_)[0]
                s = rd_cstr(val)
                note = ' ; =0x%08x' % val
                if s and 3 <= len(s) <= 48 and all(32 <= ord(c) < 127 for c in s):
                    note += ' "%s"' % s
        except Exception:
            pass
    if insn.mnemonic in ('bl', 'blx'):
        note = ''
    print(t + note)
