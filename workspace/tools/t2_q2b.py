# T2 step 8: (a) FP/numeric skeleton of each enclosing function from a REAL
# instruction boundary; (b) alignment-free pc-relative literal loader search
# for the "third addend" globals, with positive controls.
import struct, re, capstone

PAY = {'3150': r'data/servo_fw_samples/elf/v3150.bin',
       '328d8': r'data/servo_fw_samples/elf/v328d8.bin'}
TB = 0x08010000
PRO = {'3150': 0x08024864, '328d8': 0x08025398}
SITE = {'3150': 0x08024B04, '328d8': 0x080255EC}
C = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)


def img(t):
    return open(PAY[t], 'rb').read()


def dis(t, a, b):
    return list(C.disasm(img(t)[a - TB:b - TB], a))


def pc_loaders(t, targets):
    """alignment-free: find every Thumb pc-relative LDR resolving into `targets`.
    accepts both 16-bit (0x48xx) and 32-bit (0xF8DF) forms at any even offset."""
    b = img(t)
    ts = set(targets)
    out = []
    for off in range(0, len(b) - 4, 2):
        hw1 = struct.unpack_from('<H', b, off)[0]
        a = TB + off
        if (hw1 & 0xF800) == 0x4800:                     # ldr rX,[pc,#imm8*4]
            rt = (hw1 >> 8) & 7
            tgt = ((a + 4) & ~3) + ((hw1 & 0xFF) * 4)
            if tgt in ts:
                out.append((a, rt, tgt))
        elif hw1 == 0xF8DF:                              # ldr.w rX,[pc,#imm12]
            hw2 = struct.unpack_from('<H', b, off + 2)[0]
            rt = hw2 >> 12
            tgt = ((a + 4) & ~3) + (hw2 & 0xFFF)
            if tgt in ts:
                out.append((a, rt, tgt))
    return sorted(set(out))


def lit_addrs(t, glob):
    b = img(t)
    return [TB + m.start() for m in re.finditer(re.escape(struct.pack('<I', glob)), b)]


if __name__ == '__main__':
    print('########## FP / soft-float skeleton of each enclosing function')
    for t in ('3150', '328d8'):
        print('-- %s  [%08X..%08X]' % (t, PRO[t], SITE[t] + 0x80))
        for i in dis(t, PRO[t], SITE[t] + 0x80):
            mn = i.mnemonic
            if mn.startswith('v') or mn in ('bl', 'blx') or 'd0' in i.op_str:
                print('   %08X  %-10s %s' % (i.address, mn, i.op_str))
        print()

    print('########## "third addend" globals: literal pool entries and their loaders')
    for t, g in (('3150', 0x20003DB0), ('328d8', 0x20003EF8)):
        lits = lit_addrs(t, g)
        print('-- %s global 0x%08X  pool entries: %s' % (t, g, ' '.join('%08X' % x for x in lits)))
        L = pc_loaders(t, lits)
        print('   loaders found: %d' % len(L))
        for a, rt, tgt in L:
            print('   @%08X -> literal %08X (r%d):' % (a, tgt, rt))
            for i in dis(t, a, a + 14):
                print('        %08X  %-10s %s' % (i.address, i.mnemonic, i.op_str))
        print()
    print('POSITIVE CONTROL (3150 loader of 0x20003DB0 must include 08024AFE):',
          0x08024AFE in [a for a, _, _ in pc_loaders('3150', [0x08024BB0])])
