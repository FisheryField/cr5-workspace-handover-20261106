"""zf_ptrtab.py - find code that populates the RAM function-pointer tables used by
the per-axis position update routine.

D8   table base 0x20000078  (used as (**(code**)(0x20000078 + N))(..))
3150 table base 0x20000074  (per prior findings; re-derived here)

Strategy: the table lives in RAM, so its entries are written by a startup
routine from a literal/inline table.  We look for:
  a) literal dwords whose value is inside the image (candidate entries)
  b) `str` sites whose base register was loaded with the table address
  c) contiguous runs of code-address dwords (a copy source)
"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from zf_img import Img, load_pair


def app2gh(a):
    return a - 0x10000


def main():
    a, b = load_pair()
    for im, tab, labels in ((b, 0x20000078, 'D8'), (a, 0x20000074, '3150')):
        print('=' * 80)
        print('%s: table base 0x%08x' % (labels, tab))
        # (a) literal dwords pointing to the table or to the table region
        hits = im.find_u32(tab)
        print('   literal dwords equal to the table base: %s'
              % ['0x%08x' % h for h in hits])
        for h in hits:
            owners = im.xref_lit(h)
            print('      loaded by: %s' % ['0x%08x(%s)' % (i.address, i.mnemonic)
                                           for i in owners])
        # (b) who writes to the table: str with base const == tab (windowed)
        sites = im.field_sites(0, write=True)
        print('   (use zf_scan field for exact offsets)')


if __name__ == '__main__':
    sys.exit(main())
