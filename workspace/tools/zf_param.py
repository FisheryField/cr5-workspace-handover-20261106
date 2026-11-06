"""zf_param.py - search for the vendor H-parameter addressing scheme in the servo
images.

Scheme (from data/official/servoCSV/param.csv, verified in prior rounds):
    H<gg>.<ss>  ->  EtherCAT index 0x20<gg>, subIndex ss+1
                 ->  ParaMapIndex (0..259)
So the *internal* representations to look for are:
    * 0x2000 + group            (16-bit index)
    * (ss+1)                    (sub-index, small)
    * ParaMapIndex              (0..259)
    * the packed 32-bit form   group<<16 | (ss+1),  i.e. 0x20<gg>00<ss+1>

The check is a paired-presence test: if the firmware really stores a vendor
parameter table, several of these constants must coexist as a table.  A single
hit is not evidence (small integers are everywhere).

Positive control: the same scanner must find the CiA402 indices that are known
to exist (0x6040/0x6041/0x6060/0x6064/0x607A/0x607C/0x6098) via their handler
immediates.
"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from zf_img import Img, load_pair

PARAMS = {
    'H01.17 encoder position angle': (0x01, 17, 38),
    'H01.18 encoder zeroing current': (0x01, 18, 39),
    'H0C.02 encoder zeroing enable': (0x0C, 2, 189),
    'H0C.00 fault reset': (0x0C, 0, 187),
}
CIA = {0x6040: 'controlword', 0x6041: 'statusword', 0x6060: 'modes',
       0x6064: 'pos actual', 0x607A: 'target pos', 0x607C: 'home offset',
       0x6098: 'homing method'}


def main():
    a, b = load_pair()
    for im in (a, b):
        print('=' * 78)
        print(im.name)
        print('  --- positive control: CiA402 indices as immediate ---')
        for v, nm in CIA.items():
            sites = im.imm_sites(v) if hasattr(im, 'imm_sites') else None
            # simple inline scan
            out = []
            for i in im.index():
                for op in i.operands:
                    if op.type == 2 and op.imm == v:      # ARM_OP_IMM
                        out.append(i.address)
                        break
            print('    0x%04x %-14s immediate sites: %d %s'
                  % (v, nm, len(out), ['0x%08x' % x for x in out[:4]]))
        print('  --- vendor H-parameter candidates ---')
        for nm, (g, s, pm) in PARAMS.items():
            for tag, val in (('index 0x20%02X' % g, 0x2000 + g),
                             ('packed 0x20%02X00%02X' % (g, s + 1),
                              ((0x2000 + g) << 16) | (s + 1)),
                             ('ParaMapIndex', pm)):
                imm = []
                for i in im.index():
                    for op in i.operands:
                        if op.type == 2 and op.imm == val:
                            imm.append(i.address)
                            break
                lit = im.find_u32(val)
                print('    %-32s %-24s imm=%d  litdword=%d %s'
                      % (nm, tag, len(imm), len(lit),
                         ['0x%08x' % x for x in (imm[:3] + lit[:3])]))
        print()


if __name__ == '__main__':
    sys.exit(main())
