"""zf_probe1.py - top-level recon for the zero-point question.

1. How many instructions access [rX,#0x230] (OD 0x6062 field) and [rX,#0x238]
   (OD 0x6064 field), read vs write, in each image?
2. Which of those sites sit in code that also loads the constant 0x6062 /
   a descriptor base (movw #0x329)?
3. POSITIVE SELF-CHECK: a field offset that is known to exist verbatim from
   previous rounds must be found (e.g. #0x238 read site at 0x08015344/0x08014824).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from zf_img import load_pair

KNOWN = {  # offset -> (label, one known site in v328d8 per SERVO_POSCHAIN_FINDING)
    0x238: 'OD 0x6064 position actual value',
    0x230: 'OD 0x6062 (master reads this one)',
}

def main():
    a, b = load_pair()   # a = v3150, b = v328d8
    for im in (a, b):
        print('=' * 78)
        print('%s  base=0x%08x  insns=%d' % (im.name, im.base, len(im.index())))
        for off in (0x230, 0x238):
            st = im.field_sites(off)
            wr = [s for s in st if s['write']]
            rd = [s for s in st if not s['write']]
            print('  [rX,#0x%x] %-34s total=%3d  read=%3d write=%3d'
                  % (off, KNOWN[off], len(st), len(rd), len(wr)))
            for s in wr:
                bc = s['base_const']
                print('      W %08x %-9s %-26s base=%-4s const=%s'
                      % (s['addr'], s['mn'], s['op'], s['base'],
                         ('0x%08x' % bc) if bc else '-'))
    return 0

if __name__ == '__main__':
    sys.exit(main())
