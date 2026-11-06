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

def demangle(m):
    table = {
        '_ZNK4Json5Value6asBoolEv': 'Json::asBool',
        '_ZN14DataSubProcess10clearErrorEv': 'DataSubProcess::clearError',
        '_ZNSsC1EPKcRKSaIcE': 'std::string(char*)',
        '_ZNK9rapidjson12GenericValueINS_4UTF8IcEENS_19MemoryPoolAllocatorINS_12CrtAllocatorEEEE9HasMemberEPKc': 'rj::HasMember',
        '_ZN4Json5ValueixEPKc': 'Json::op[]',
        '_ZNK4Json5Value6isNullEv': 'Json::isNull',
        '_ZN4Json5ValueC1ERKS0_': 'Json::Value ctor',
        '_ZNKSs7compareEPKc': 'str::compare',
        '_ZNSs6assignEPKc': 'str::assign',
        '_ZN14DataSubProcess5ReplyEb': 'Reply(bool)',
        '_ZN14DataSubProcess5ReplyERSs': 'Reply(str)',
        '_ZN14DataSubProcess10caliHomeEv': 'DataSubProcess::caliHome()',
        '_ZN12robot_control8caliHomeEv': 'robot_control::caliHome()',
    }
    return table.get(m, m)

# symbol table not needed - known bounds from checkpoint: caliHome@0xF0428, 224 B
for addr, label, ksz in [(0x000F0428, 'caliHome', 224)]:
    print('=== %s @0x%x size=%d ===' % (label, addr, ksz))
    LO, HI = addr, addr + ksz + 64
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
                    vv = struct.unpack_from('<I', e.d, lo_)[0]
                    pend[reg] = vv
                    s = cstr(vv) if vv > 0x200000 else None
                    note = ' ; =0x%x' % vv + (' "%s"' % s if s else '')
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
            note += '  <%s>' % demangle(sym) if sym else '  <?0x%x>' % tgt
        for v in smap.get(insn.address, []):
            s = cstr(v)
            note += '  [STR "%s"]' % (s if s else hex(v))
        print('%08x  %-8s %-42s%s' % (insn.address, insn.mnemonic, op, note))
