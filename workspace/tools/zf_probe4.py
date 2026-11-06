"""zf_probe4.py - locate the persistence routines in BOTH images by structure
(not by address) and print them instruction-by-instruction so the two can be
compared role by role.

Anchors (per SERVO_PERSIST_FINDING, re-derived here):
  * magic 0xA1B2C3D4  -> parameter-persistence header
  * magic 0xBE6D4A8B  -> flash log record header
  * flash unlock keys 0x45670123 / 0xCDEF89AB
"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from zf_img import Img, load_pair


def func_start(im, addr, back=0x600):
    """walk back from addr to the previous 'push {...lr}' / 'push.w' so we can
    print a whole function body."""
    insns = [i for i in im.index() if addr - back <= i.address <= addr]
    last = None
    for i in insns:
        if i.mnemonic in ('push', 'push.w') and 'lr' in i.op_str:
            last = i.address
    return last or (addr - 0x80)


def show(im, start, length, label=''):
    print('#### %s  %s  0x%08x..0x%08x' % (im.name, label, start, start + length))
    for i in im.dis(start, length):
        lit = im.lit_of(i)
        note = ''
        if lit:
            note = '   ; lit@0x%08x = 0x%08x' % lit
        c = im.call(i)
        if c is not None:
            note += '   ; ->0x%08x' % c
        if i.mnemonic.startswith('b') and i.mnemonic not in ('bic', 'bfi', 'bfc') and i.op_str.startswith('#'):
            note += '   ; =>0x%08x' % (int(i.op_str[1:], 0) & ~1)
        print('  %08x: %-10s %-30s%s' % (i.address, i.mnemonic, i.op_str, note))
    print()


def main():
    a, b = load_pair()   # a=v3150 b=v328d8
    # 1) persistence routine that uses magic 0xA1B2C3D4
    for im, magic_addr in ((a, 0x08011800), (b, 0x080117c0)):
        # find the ldr that loads this literal
        owners = im.xref_lit(magic_addr)
        print('%s: magic-lit owners: %s' % (im.name, ['0x%08x' % i.address for i in owners]))
        for o in owners:
            s = func_start(im, o.address)
            print('   function containing 0x%08x starts 0x%08x' % (o.address, s))
    print()
    # 2) flash log routine using magic 0xBE6D4A8B
    for im, magic_addr in ((a, 0x08011894), (b, 0x08011854)):
        owners = im.xref_lit(magic_addr)
        print('%s: log-magic owners: %s' % (im.name, ['0x%08x' % i.address for i in owners]))
        for o in owners:
            s = func_start(im, o.address)
            print('   function containing 0x%08x starts 0x%08x' % (o.address, s))
    print()
    # 3) who loads the unlock keys
    for im, (k1, k2) in ((a, (0x0801416c, 0x08014170)), (b, (0x08014508, 0x0801450c))):
        o1 = im.xref_lit(k1)
        print('%s: FLASH_KEY1 owners: %s' % (im.name, ['0x%08x' % i.address for i in o1]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
