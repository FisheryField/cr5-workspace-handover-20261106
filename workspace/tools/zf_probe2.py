"""zf_probe2.py - disassemble around the two real [rBase,#0x230] writers in each
image and print enough context to read the dataflow by hand.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from zf_img import load_pair

def show(im, center, before=0x40, after=0x30):
    at = center - before
    print('---- %s  @0x%08x ----' % (im.name, center))
    for i in im.dis(center - before, before + after):
        mark = '  <<<' if i.address == center else ''
        lit = im.lit_of(i)
        note = ''
        if lit:
            note = '   ; =0x%08x' % lit[1]
        c = im.call(i)
        if c is not None:
            note += '   ; ->0x%08x' % c
        print('  %08x: %-10s %-30s%s%s' % (i.address, i.mnemonic, i.op_str, note, mark))
    print()

def main():
    a, b = load_pair()
    for im, sites in ((a, (0x0802f87c, 0x0802f98a)),
                      (b, (0x08030c38, 0x08030d58))):
        for s in sites:
            show(im, s)
    return 0

if __name__ == '__main__':
    sys.exit(main())
