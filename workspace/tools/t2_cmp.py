# T2 step 4: window around each store, normalized sequence diff,
# and field-access census of the "third addend" globals.
import struct, re, difflib, capstone

PAY = {'3150': r'data/servo_fw_samples/elf/v3150.bin',
       '328d8': r'data/servo_fw_samples/elf/v328d8.bin'}
TRUE_BASE = 0x08010000
SITE = {'3150': 0x08024B04, '328d8': 0x080255EC}
PRO = {'3150': 0x08024864, '328d8': 0x08025398}
G = {'3150': 0x20003DB0, '328d8': 0x20003EF8}
C = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)


def img(t):
    return open(PAY[t], 'rb').read()


def dis(t, a, b):
    return list(C.disasm(img(t)[a - TRUE_BASE:b - TRUE_BASE], a))


REG = re.compile(r'\b(?:r\d+|sb|sl|fp|ip|sp|lr|pc)\b')


def norm(i):
    """token: mnemonic(normalized) + immediates + fp types + memory offsets,
    registers masked so the two builds' allocation differences do not dominate."""
    m = i.mnemonic
    m = m.replace('.w', '').replace('.n', '')
    ops = REG.sub('R', i.op_str)
    ops = re.sub(r'\s+', ' ', ops)
    return '%s %s' % (m, ops)


def skeleton_tokens(t, a, b):
    keep = ('mov', 'movs', 'movw', 'movt', 'add', 'adds', 'addw', 'sub', 'subs',
            'subw', 'rsb', 'mul', 'muls', 'mla', 'mls', 'smull', 'umull', 'umlal',
            'sdiv', 'udiv', 'lsl', 'lsls', 'lsr', 'lsrs', 'asr', 'asrs', 'and',
            'ands', 'orr', 'orrs', 'eor', 'cmp', 'cmn', 'vadd', 'vsub', 'vmul',
            'vdiv', 'vcvt', 'vmov', 'vneg', 'vabs', 'vldr', 'vstr', 'vmrs')
    out = []
    for i in dis(t, a, b):
        if i.mnemonic.split('.')[0] in keep:
            out.append(norm(i))
    return out


def pcref_map(t):
    """address of literal -> list of instruction addresses that load it"""
    b = img(t)
    end = 0x08010000 + len(b)
    m = {}
    for i in C.disasm(b, TRUE_BASE):
        if i.mnemonic.startswith('ldr') and i.operands:
            o = i.operands[0] if len(i.operands) == 1 else i.operands[1]
            if o.type == capstone.arm.ARM_OP_MEM and o.mem.base == capstone.arm.ARM_REG_PC:
                tgt = (i.address + 4) & ~3
                tgt += o.mem.disp
                m.setdefault(tgt, []).append(i.address)
    return m


def field_census(t, glob):
    b = img(t)
    refs = [TRUE_BASE + mm.start() for mm in re.finditer(re.escape(struct.pack('<I', glob)), b)]
    pm = pcref_map(t)
    print('== %s global 0x%08X : pool entries %s' % (t, glob, ' '.join('%08X' % r for r in refs)))
    for r in refs:
        loaders = pm.get(r, [])
        print('   pool %08X  loaded by %s' % (r, ' '.join('%08X' % x for x in loaders) or 'NONE'))
        for L in loaders:
            for i in dis(t, L, L + 12):
                print('        %08X  %-9s %s' % (i.address, i.mnemonic, i.op_str))
    print()


if __name__ == '__main__':
    for t in ('3150', '328d8'):
        print('############ %s  WINDOW around store %08X' % (t, SITE[t]))
        for i in dis(t, SITE[t] - 0x34, SITE[t] + 0x40):
            mark = '  <<<' if i.address == SITE[t] else ''
            print('  %08X  %-10s %s%s' % (i.address, i.mnemonic, i.op_str, mark))
        print()
    print('############ normalized numeric-skeleton diff (prologue -> store)')
    A = skeleton_tokens('3150', PRO['3150'], SITE['3150'])
    B = skeleton_tokens('328d8', PRO['328d8'], SITE['328d8'])
    sm = difflib.SequenceMatcher(None, A, B, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            print('  =  %2d lines identical' % (i2 - i1))
        else:
            print('  %s 3150[%d:%d] %s' % (tag.upper(), i1, i2, ' | '.join(A[i1:i2])))
            print('       d8 [%d:%d] %s' % (j1, j2, ' | '.join(B[j1:j2])))
    print('  ratio %.3f  (3150 %d / d8 %d numeric insns)' % (sm.ratio(), len(A), len(B)))
    print()
    for t in ('3150', '328d8'):
        field_census(t, G[t])
