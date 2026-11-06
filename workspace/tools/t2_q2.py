# T2 step 7: identify each build's normalization struct base, test whether D8
# reads an analogous "third addend", and census the +0.5 / -0.5 rounding signs.
import struct, capstone

PAY = {'3150': r'data/servo_fw_samples/elf/v3150.bin',
       '328d8': r'data/servo_fw_samples/elf/v328d8.bin'}
TB = 0x08010000
C = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
KNOWN_SUB = 0x0802555E          # positive control: D8 vsub.f32 by 0.5


def img(t):
    return open(PAY[t], 'rb').read()


def dis(t, a, b):
    return list(C.disasm(img(t)[a - TB:b - TB], a))


def pool(t, a, b):
    d = img(t)[a - TB:b - TB]
    print('--- %s pool [%08X..%08X]' % (t, a, b))
    for off in range(0, len(d) - 3, 4):
        print('   %08X : %08X' % (a + off, struct.unpack_from('<I', d, off)[0]))
    print()


def loaders_of(t, glob):
    """instructions whose pc-relative literal == glob"""
    b = img(t)
    hits = []
    for i in C.disasm(b, TB):
        if i.mnemonic.startswith('ldr') and len(i.operands) == 2:
            o = i.operands[1]
            if o.type == capstone.arm.ARM_OP_MEM and o.mem.base == capstone.arm.ARM_REG_PC:
                if ((i.address + 4) & ~3) + o.mem.disp == glob:
                    hits.append(i.address)
    return hits


if __name__ == '__main__':
    pool('328d8', 0x08025600, 0x08025630)
    pool('3150', 0x08024980, 0x080249B0)

    print('== rounding census: vmov.f32 sX,#5.0e-01 and the following FP op')
    for t in ('3150', '328d8'):
        b = img(t)
        li = list(C.disasm(b, TB))
        idx = {i.address: k for k, i in enumerate(li)}
        found = []
        for k, i in enumerate(li):
            if i.mnemonic == 'vmov.f32' and '5.000000e-01' in i.op_str:
                nxt = li[k + 1] if k + 1 < len(li) else None
                nn = li[k + 2] if k + 2 < len(li) else None
                found.append('%08X %s -> %s %s -> %s %s' % (
                    i.address, i.op_str,
                    nxt.mnemonic if nxt else '?', nxt.op_str if nxt else '',
                    nn.mnemonic if nn else '?', nn.op_str if nn else ''))
        print('-- %s : %d site(s)' % (t, len(found)))
        for x in found:
            print('    ', x)
        print('     positive control present:',
              any(x.startswith('%08X' % KNOWN_SUB) for x in found) if t == '328d8' else 'n/a')

    print()
    print('== literals 0x20003DB0 (3150) / 0x20003EF8 (D8) : loaders + following insns')
    for t, g in (('3150', 0x20003DB0), ('328d8', 0x20003EF8)):
        L = loaders_of(t, g)
        print('-- %s  0x%08X : %d loader(s) %s' % (t, g, len(L), ' '.join('%08X' % x for x in L)))
        for a in L:
            for i in dis(t, a, a + 14):
                print('     %08X  %-10s %s' % (i.address, i.mnemonic, i.op_str))
            print()
