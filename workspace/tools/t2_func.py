# T2 step 3: recover the enclosing function of each +0x234 store, dump both,
# and produce a normalized "numeric skeleton" diff (constants / FP / width).
import struct, re, capstone

PAY = {'3150': r'data/servo_fw_samples/elf/v3150.bin',
       '328d8': r'data/servo_fw_samples/elf/v328d8.bin'}
TRUE_BASE = 0x08010000
SITE = {'3150': 0x08024B04, '328d8': 0x080255EC}
C = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)


def img(tag):
    return open(PAY[tag], 'rb').read()


def insns(tag, start, end):
    b = img(tag)
    return list(C.disasm(b[start - TRUE_BASE:end - TRUE_BASE], start))


def prologue_before(tag, site, back=0x600):
    """nearest 'push {...lr}' whose linear disassembly reaches `site` exactly."""
    b = img(tag)
    best = None
    for off in range(site - TRUE_BASE - back, site - TRUE_BASE):
        if off < 0:
            continue
        hw = struct.unpack_from('<H', b, off)[0]
        is16 = (hw & 0xFF00) == 0xB500 or (hw & 0xFE00) == 0xB400  # push {..,lr}
        is32 = struct.unpack_from('<H', b, off)[0] == 0xE92D            # push.w
        if not (is16 or is32):
            continue
        start = TRUE_BASE + off
        li = insns(tag, start, site + 4)
        if li and li[-1].address == site:
            best = start
    return best


def skeleton(tag, start, end):
    """numeric/arithmetic instructions only: drop pure loads/stores/branches."""
    keep = ('mov', 'movs', 'movw', 'movt', 'add', 'adds', 'addw', 'sub', 'subs',
            'subw', 'rsb', 'mul', 'muls', 'mla', 'mls', 'smull', 'umull', 'umlal',
            'sdiv', 'udiv', 'lsl', 'lsls', 'lsr', 'lsrs', 'asr', 'asrs', 'and',
            'ands', 'orr', 'orrs', 'eor', 'cmp', 'cmn', 'vadd', 'vsub', 'vmul',
            'vdiv', 'vcvt', 'vmov', 'vneg', 'vabs', 'vldr', 'vstr', 'vmrs')
    out = []
    for i in insns(tag, start, end):
        base = i.mnemonic.split('.')[0]
        out.append(('%s %s' % (i.mnemonic, i.op_str)) if base in keep else None)
    return out


if __name__ == '__main__':
    info = {}
    for tag in ('3150', '328d8'):
        s = prologue_before(tag, SITE[tag])
        assert s, ('no prologue found for ' + tag)
        info[tag] = s
        li = insns(tag, s, SITE[tag] + 0x90)
        with open('tools/t2_%s.txt' % tag, 'w', encoding='utf-8') as f:
            for i in li:
                f.write('%08X  %-10s %s\n' % (i.address, i.mnemonic, i.op_str))
        print('%-6s prologue TRUE %08X  store %08X  body %d insns -> tools/t2_%s.txt'
              % (tag, s, SITE[tag], len(li), tag))
    print()
    for tag in ('3150', '328d8'):
        sk = skeleton(tag, info[tag], SITE[tag])
        print('== %s numeric skeleton from prologue to store (%d numeric insns)' % (tag, sum(1 for x in sk if x)))
        for x in sk:
            if x:
                print('   ', x)
        print()
