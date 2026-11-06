# T2: independent re-check of the +0x234 construction in v3150 vs v328d8.
# Address convention: TRUE flash addr = 0x08010000 + file offset (task rule).
# We verify the rule empirically from the vector table before trusting it.
import struct, sys, capstone

PAY = {'3150': r'data/servo_fw_samples/elf/v3150.bin',
       '328d8': r'data/servo_fw_samples/elf/v328d8.bin'}
ELF = {'3150': r'data/servo_fw_samples/elf/v3150.elf',
       '328d8': r'data/servo_fw_samples/elf/v328d8.elf'}


def load(tag):
    img = open(PAY[tag], 'rb').read()
    e = open(ELF[tag], 'rb').read()
    shoff = struct.unpack_from('<I', e, 32)[0]
    shentsize = struct.unpack_from('<H', e, 46)[0]
    name, typ, flags, addr, off, size, *_ = struct.unpack_from('<10I', e, shoff + 1 * shentsize)
    txt = e[off:off + size]
    assert txt == img, (tag, 'elf .text != payload')
    return img


def md(tag):
    m = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    m.detail = True
    base = 0x08010000          # TRUE addressing
    img = load(tag)
    m.disasm(img, base, count=0)
    return m, img, base


def show(tag, off, n, label=''):
    m, img, base = md(tag)
    print('=== %s  file_off 0x%X  true_addr 0x%X  %s' % (tag, off, base + off, label))
    for ins in m.disasm(img[off:off + n], base + off):
        print('  %08X  %-8s %s' % (ins.address, ins.mnemonic, ins.op_str))
    print()


def count_store234(tag):
    """positive control: find every store to [rX,#0x234] in the whole image."""
    m, img, base = md(tag)
    hits = []
    for ins in m.disasm(img, base):
        if ins.mnemonic in ('str.w', 'str') and '#0x234' in ins.op_str:
            hits.append((ins.address, ins.mnemonic, ins.op_str))
    return hits


if __name__ == '__main__':
    for tag in ('3150', '328d8'):
        img = load(tag)
        w = struct.unpack_from('<8I', img, 0)
        print(tag, 'len=0x%X' % len(img), 'first8words:', ' '.join('%08X' % x for x in w))
    print()
    print('---- positive control: stores to #0x234 ----')
    for tag in ('3150', '328d8'):
        h = count_store234(tag)
        print(tag, len(h))
        for a, mn, ops in h:
            print('   %08X %s %s' % (a, mn, ops))
