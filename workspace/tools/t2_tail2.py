# T2 step 6: normalization segments (-> +0xA8/+0xB0), numeric constant census
# in the enclosing function, and a saturation-op census with positive control.
import struct, re, capstone

PAY = {'3150': r'data/servo_fw_samples/elf/v3150.bin',
       '328d8': r'data/servo_fw_samples/elf/v328d8.bin'}
TB = 0x08010000
C = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
PRO = {'3150': 0x08024864, '328d8': 0x08025398}
SITE = {'3150': 0x08024B04, '328d8': 0x080255EC}


def img(t):
    return open(PAY[t], 'rb').read()


def dis(t, a, b):
    return list(C.disasm(img(t)[a - TB:b - TB], a))


def show(t, a, b, label):
    print('--- %s %s [%08X..%08X]' % (t, label, a, b))
    for i in dis(t, a, b):
        print('   %08X  %-10s %s' % (i.address, i.mnemonic, i.op_str))
    print()


def nconst(t, a, b):
    """every immediate >= 0x100 in the range, as a numeric census"""
    out = []
    for i in dis(t, a, b):
        for m in re.finditer(r'#0x([0-9a-f]+)', i.op_str):
            v = int(m.group(1), 16)
            if v >= 0x100:
                out.append('%08X %s %s' % (i.address, i.mnemonic, i.op_str))
                break
    return out


def find_store(t, off):
    b = img(t)
    hits = []
    for i in range(len(b) - 4):
        hw1 = struct.unpack_from('<H', b, i)[0]
        hw2 = struct.unpack_from('<H', b, i + 2)[0]
        if (hw1 & 0xFFF0) == 0xF8C0 and (hw2 & 0x0FFF) == off:
            hits.append(TB + i)
    return hits


if __name__ == '__main__':
    print('== stores to #0xb0 (328d8) / #0xa8 (3150)')
    for t, o in (('328d8', 0xB0), ('3150', 0xA8)):
        print('   %s #0x%02X : %s' % (t, o, ' '.join('%08X' % x for x in find_store(t, o))))
    print()
    show('3150', 0x08024A3C, 0x08024AE0, 'normalization -> +0xA8')
    show('328d8', 0x08025520, 0x080255E0, 'normalization -> +0xB0')
    print('== immediates >= 0x100 inside the enclosing function (prologue..store+0x80)')
    for t in ('3150', '328d8'):
        print('-- %s' % t)
        for x in nconst(t, PRO[t], SITE[t] + 0x80):
            print('   ', x)
    print()
    print('== saturation / rounding instruction census (whole image)')
    for t in ('3150', '328d8'):
        b = img(t)
        cnt = {}
        for i in C.disasm(b, TB):
            b0 = i.mnemonic.split('.')[0]
            if b0 in ('ssat', 'usat', 'ssat16', 'usat16', 'qadd', 'qsub', 'qdadd',
                      'qdsub', 'vqmovn', 'vqadd', 'vqsub', 'vcvt', 'vrinta',
                      'vrintn', 'vrintp', 'vrintm', 'vrintz', 'vrintr'):
                cnt[b0] = cnt.get(b0, 0) + 1
        print('   %s : %s' % (t, sorted(cnt.items())))
