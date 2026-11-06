import sys, struct
sys.path.insert(0, 'tools')
sys.path.insert(0, '.pylibs')
import libdata_strrefs as L
import libdata_plt as P
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

e = L.Elf()
d, secs, stub, slot2sym, dsym, plt, rel = P.build()
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

def demangle_short(m):
    if not m:
        return None
    # crude demangle of the common names we care about
    table = {
        '_ZNK4Json5Value6asBoolEv': 'Json::Value::asBool()',
        '_ZN14DataSubProcess10clearErrorEv': 'DataSubProcess::clearError()',
        '_ZNSsC1EPKcRKSaIcE': 'std::string(char*)',
        '_ZNK9rapidjson12GenericValueINS_4UTF8IcEENS_19MemoryPoolAllocatorINS_12CrtAllocatorEEEE9HasMemberEPKc': 'rj::HasMember',
        '_ZN9rapidjson12GenericValueINS_4UTF8IcEENS_19MemoryPoolAllocatorINS_12CrtAllocatorEEEEixIKcEENS_8internal9DisableIfINS9_15RemoveSfinaeTagIPFRNS9_9SfinaeTagENS9_7NotExprINS9_6IsSameINS9_11RemoveConstIT_E4TypeEcEEEEEE4TypeERS6_E4TypeEPSH_': 'rj::operator[]',
        '_ZNSs6assignEPKc': 'std::string::assign',
        '_ZNKSs7compareEPKc': 'std::string::compare',
        '_ZN4Json5ValueixEPKc': 'Json::Value::operator[]',
        '_ZNK4Json5Value6isNullEv': 'Json::Value::isNull()',
        '_ZN4Json5ValueC1ERKS0_': 'Json::Value ctor',
    }
    if m in table:
        return table[m]
    if m.startswith('_Z'):
        return m  # keep raw
    return m

LO, HI = 0x11a1ac, 0x11a5c0   # modifyServoParams body (1016 B)
sites = L.scan(e)
smap = {}
for a, v in sites:
    smap.setdefault(a, []).append(v)

pend = {}
for insn in md.disasm(e.d[v2o(LO):v2o(LO)+(HI-LO)], LO):
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
    if insn.mnemonic in ('bl', 'blx') and op.startswith('#'):
        tgt = int(op[1:], 0)
        sym = stub.get(tgt) or stub.get(tgt & ~1)
        if sym:
            note += '  <%s>' % demangle_short(sym)
        else:
            note += '  <??>'
    for v in smap.get(insn.address, []):
        s = cstr(v)
        note += '  [STRREF "%s"]' % (s if s else hex(v))
    print('%08x  %-8s %-44s%s' % (insn.address, insn.mnemonic, op, note))
