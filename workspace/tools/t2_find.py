# T2 step 2: locate the real sites by instruction encoding + literal-pool scan.
import struct, re, capstone

PAY = {'3150': r'data/servo_fw_samples/elf/v3150.bin',
       '328d8': r'data/servo_fw_samples/elf/v328d8.bin'}
TRUE_BASE = 0x08010000


def img(tag):
    return open(PAY[tag], 'rb').read()


def m():
    c = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    c.detail = True
    return c


def dis(tag, off, n, label=''):
    b = img(tag)
    c = m()
    print('--- %s  file 0x%X  TRUE 0x%X  %s' % (tag, off, TRUE_BASE + off, label))
    for ins in c.disasm(b[off:off + n], TRUE_BASE + off):
        print('   %08X  %-9s %s' % (ins.address, ins.mnemonic, ins.op_str))
    print()


def sites_str234(tag):
    """str.w rX,[rY,#0x234]  ->  enc bytes: 0xF8C0|Rn , Rt | (0x234<<4)"""
    b = img(tag)
    out = []
    for i in range(len(b) - 4):
        hw1 = struct.unpack_from('<H', b, i)[0]
        hw2 = struct.unpack_from('<H', b, i + 2)[0]
        if (hw1 & 0xFFF0) == 0xF8C0 and (hw2 & 0x0FFF) == 0x234:
            out.append((TRUE_BASE + i, hw1 & 0xF, hw2 >> 12))
    return out


def lit_refs(tag, value, maxn=200):
    """little-endian dword occurrences of an address constant (literal pools)."""
    b = img(tag)
    pat = struct.pack('<I', value)
    return [TRUE_BASE + mm.start() for mm in re.finditer(re.escape(pat), b)][:maxn]


if __name__ == '__main__':
    # positive control for the base rule: reset handler must be a real prologue
    for tag in ('3150', '328d8'):
        b = img(tag)
        print(tag, 'bytes @file 0x19C (reset handler 0x0801019C):', b[0x19C:0x1A6].hex(' '))
    print()
    for tag in ('3150', '328d8'):
        s = sites_str234(tag)
        print('== %s  str.w rX,[rY,#0x234] sites: %d' % (tag, len(s)))
        for a, rn, rt in s:
            print('   TRUE %08X  Rt=r%d Rn=r%d' % (a, rt, rn))
    print()
    for tag in ('3150', '328d8'):
        for v in (0x20003DB0, 0x20000078, 0x20000074, 0x20003EF8):
            r = lit_refs(tag, v)
            print('%s  lit 0x%08X : %d  %s' % (tag, v, len(r), ' '.join('%08X' % x for x in r[:12])))
        print()
