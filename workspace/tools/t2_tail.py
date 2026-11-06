# T2 step 5: tails (the call path to +0x238), literal pools, and the
# normalization segment that produces +0xA8 (3150) / +0xB0 (D8).
import struct, capstone, re

PAY = {'3150': r'data/servo_fw_samples/elf/v3150.bin',
       '328d8': r'data/servo_fw_samples/elf/v328d8.bin'}
TB = 0x08010000
C = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)


def img(t):
    return open(PAY[t], 'rb').read()


def dis(t, a, b):
    return list(C.disasm(img(t)[a - TB:b - TB], a))


def show(t, a, b, label):
    print('--- %s %s [%08X..%08X]' % (t, label, a, b))
    for i in dis(t, a, b):
        print('   %08X  %-10s %s' % (i.address, i.mnemonic, i.op_str))
    print()


def pool(t, a, b, label):
    d = img(t)[a - TB:b - TB]
    print('--- %s literal pool %s [%08X..%08X]' % (t, label, a, b))
    for off in range(0, len(d) - 3, 4):
        v = struct.unpack_from('<I', d, off)[0]
        tag = ''
        if 0x20000000 <= v < 0x20020000:
            tag = '  <-- RAM global'
        print('   %08X : %08X%s' % (a + off, v, tag))
    print()


def find_store(t, off, rn_op):
    """where the normalization result is stored (the +0xA8 / +0xB0 write)."""
    b = img(t)
    hits = []
    for i in range(len(b) - 4):
        hw1 = struct.unpack_from('<H', b, i)[0]
        hw2 = struct.unpack_from('<H', b, i + 2)[0]
        if (hw1 & 0xFFF0) == 0xF8C0 and (hw2 & 0x0FFF) == off:
            hits.append(TB + i)
    return hits


if __name__ == '__main__':
    show('3150', 0x08024B40, 0x08024B74, 'tail after store (call path to +0x238)')
    show('328d8', 0x080255EE, 0x0802560A, 'tail after store (call path to +0x238)')
    pool('3150', 0x08024B98, 0x08024BC0, 'A')
    pool('328d8', 0x0802562C, 0x08025640, 'D8')
    print('== stores to #0xb0 (D8) / #0xa8 (3150) anywhere in image')
    for t, o in (('328d8', 0xB0), ('3150', 0xA8)):
        print('  %s #0x%02X :' % (t, o), ' '.join('%08X' % x for x in find_store(t, o)))
    print()
    show('328d8', 0x08025560, 0x080255E0, 'normalization segment -> +0xB0')
    show('3150', 0x08024A60, 0x08024AE0, '~normalization segment -> +0xA8 (search below)')
