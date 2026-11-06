import sys, struct
sys.path.insert(0, '.pylibs')
import capstone

SO = 'libdataSvr.so.bin'
data = open(SO, 'rb').read()
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

md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.detail = True

# Disassemble whole exec segment once; track pending literal loads per reg;
# on 'add reg, pc' compute final and check against target strings.
TARGETS = {0x214a74: 'clear error from http exchange ....',
           0x214a9c: 'clear error from http exchange done !'}

ex = [s for s in segs if s[0] == 0][0] if False else None
# choose the segment that contains 0x11a000 (text)
seg = None
for va, off, sz in segs:
    if va <= 0x11a000 < va + sz:
        seg = (va, off, sz)
        break
print('text seg', hex(seg[0]), hex(seg[1]), hex(seg[2]))
va, off, sz = seg
code = data[off:off+sz]
found = 0
pend = {}
for insn in md.disasm(code, va):
    op = insn.op_str
    if insn.mnemonic.startswith('ldr') and '[pc' in op and ',' in op:
        try:
            reg = op.split(',')[0].strip()
            imm = int(op.split('#')[-1].rstrip(']'), 0)
            pc = (insn.address + 4) & ~3
            lo_ = v2o(pc + imm)
            if lo_ is not None:
                pend[reg] = struct.unpack_from('<I', data, lo_)[0]
        except Exception:
            pass
    elif insn.mnemonic == 'add' and op.endswith(', pc'):
        reg = op.split(',')[0].strip()
        if reg in pend:
            final = pend[reg] + insn.address + 4
            if final in TARGETS:
                print('%08x  %s %s -> "%s"' % (insn.address, insn.mnemonic, op, TARGETS[final]))
                found += 1
            del pend[reg]
    else:
        # any instruction that redefines the register kills the pending state
        try:
            dst = op.split(',')[0].strip()
            if dst in pend and insn.mnemonic not in ('cmp', 'mov', 'nop', 'str', 'push'):
                del pend[dst]
        except Exception:
            pass
print('found', found)
