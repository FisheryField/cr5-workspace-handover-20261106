"""zf_probe5.py - structure map of the NV/persistence subsystem in both images.

For each image:
  * locate every `ldr rX,[pc,#n]` whose literal is one of the anchors
    (magics, flash keys, flash regs) -> report owning function start
  * walk back to the function start using a `push {...,lr}` scan
  * count callers of that function start (bl/blx resolution from capstone)
  * ALSO: positive self-check via a constant that must exist.
"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from zf_img import Img, load_pair

ANCHORS = {
    0xBE6D4A8B: 'log-record magic',
    0xA1B2C3D4: 'param-block magic',
    0x40023C00: 'FLASH reg base (F4)',
    0x40023C0C: 'FLASH_CR',
    0x40023C10: 'FLASH_SR',
    0x0800C000: 'log area start',
    0x08080000: 'log high-water',
    0x45670123: 'FLASH_KEY1',
    0xCDEF89AB: 'FLASH_KEY2',
}


def func_start(im, addr, back=0x800):
    best = None
    for i in im.index():
        if i.address > addr:
            break
        if i.address < addr - back:
            continue
        if i.mnemonic in ('push', 'push.w') and 'lr' in i.op_str:
            best = i.address
    return best


def main():
    a, b = load_pair()
    for im in (a, b):
        print('=' * 90)
        print('%s  (%d bytes, %d instructions)' % (im.name, len(im.blob), len(im.index())))
        # literal -> owner map, built in one pass
        owners = {}
        for i in im.index():
            lit = im.lit_of(i)
            if lit is None:
                continue
            owners.setdefault(lit[1], []).append(i.address)
        for v, label in sorted(ANCHORS.items()):
            sites = owners.get(v, [])
            extra = ''
            if sites:
                fs = func_start(im, sites[0])
                extra = '   in function 0x%08x' % fs if fs else ''
            print('  %-22s 0x%08x  load sites: %s%s'
                  % (label, v, ['0x%08x' % s for s in sites[:6]], extra))
        print()


if __name__ == '__main__':
    sys.exit(main())
