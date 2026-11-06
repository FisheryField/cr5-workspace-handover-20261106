import sys, struct
sys.path.insert(0, 'tools')
sys.path.insert(0, '.pylibs')
import libdata_strrefs as L
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

e = L.Elf()
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True

LO, HI = 0x11a700, 0x11ac00
o = e.v2o(LO) if hasattr(e, 'v2o') else None
if o is None:
    # build a mapper from section headers
    def v2o(v):
        for s in e.secs:
            if s['addr'] <= v < s['addr'] + s['size']:
                return s['offset'] + (v - s['addr'])
        return None
else:
    v2o = e.v2o

def cstr(v):
    for s in e.secs:
        if s['addr'] <= v < s['addr'] + s['size']:
            oo = s['offset'] + (v - s['addr'])
            end = e.d.find(b'\0', oo, oo + 100)
            if end < 0:
                return None
            b = e.d[oo:end]
            if b and all(32 <= c < 127 for c in b):
                return b.decode()
    return None

sites = L.scan(e)
smap = {}
for a, v in sites:
    smap.setdefault(a, []).append(v)

o = v2o(LO)
code = e.d[o:o + (HI - LO)]
pend = {}
for insn in md.disasm(code, LO):
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
                s = cstr(val) if val > 0x200000 else None
                note = ' ; pool=0x%x' % val + (' "%s"' % s if s else '')
        except Exception:
            pass
    elif insn.mnemonic == 'add' and op.endswith(', pc'):
        reg = op.split(',')[0].strip()
        if reg in pend:
            final = pend[reg] + insn.address + 4
            s = cstr(final)
            note = ' ; -> 0x%x' % final + (' "%s"' % s if s else '')
            del pend[reg]
    for v in smap.get(insn.address, []):
        s = cstr(v)
        note += '  [STRREF "%s"]' % (s if s else hex(v))
    print('%08x  %-8s %-46s%s' % (insn.address, insn.mnemonic, op, note))
