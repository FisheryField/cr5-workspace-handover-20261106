import sys, struct
sys.path.insert(0, 'tools')
sys.path.insert(0, '.pylibs')
import libdata_strrefs as L
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

e = L.Elf()
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

def v2o(v):
    for s in e.secs:
        if s['addr'] <= v < s['addr'] + s['size']:
            return s['offset'] + (v - s['addr'])
    return None

def cstr(v):
    for s in e.secs:
        if s['addr'] <= v < s['addr'] + s['size']:
            oo = s['offset'] + (v - s['addr'])
            end = e.d.find(b'\0', oo, oo + 120)
            if end < 0:
                return None
            b = e.d[oo:end]
            if b and all(32 <= c < 127 for c in b):
                return b.decode()
    return None

# disassemble the PLT-thunk region for 0xb957c and the target function briefly
for target, name in [(0xb957c, 'judge@0x11aadc'), (0xb6530, 'clearAction@0x11ab0a')]:
    print('===', name, hex(target), '===')
    o = v2o(target)
    code = e.d[o:o+160]
    pend = {}
    for insn in md.disasm(code, target):
        note = ''
        op = insn.op_str
        if insn.mnemonic.startswith('ldr') and '[pc' in op and ',' in op:
            try:
                reg = op.split(',')[0].strip()
                imm = int(op.split('#')[-1].rstrip(']'), 0)
                pc = (insn.address + 4) & ~3
                lo_ = v2o(pc + imm)
                if lo_ is not None:
                    val = struct.unpack_from('<I', e.d, lo_)[0]
                    pend[reg] = val
                    note = ' ; pool=0x%x' % val
            except Exception:
                pass
        elif insn.mnemonic == 'add' and op.endswith(', pc'):
            reg = op.split(',')[0].strip()
            if reg in pend:
                final = pend[reg] + insn.address + 4
                s = cstr(final)
                note = ' ; -> 0x%x' % final + (' "%s"' % s if s else '')
                del pend[reg]
        print('%08x  %-8s %-40s%s' % (insn.address, insn.mnemonic, op, note))
        if insn.mnemonic in ('pop', 'bx') and 'pc' in op:
            break
