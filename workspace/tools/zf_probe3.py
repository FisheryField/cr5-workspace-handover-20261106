"""zf_probe3.py - parameter index search + persistence API call-frame census.

A. Positive self-check: search for constants that ARE known to be present
   (20000 = 0x4E20 as a movw immediate; flash keys; magic values).
B. Search for the vendor parameter indices 0x2001 / 0x200C and the
   ParaMapIndex values 38 / 189 / 39 (as immediates and as literal dwords),
   including the "0x20<group>" 16-bit form.
C. Locate the persistence API chain: 0x080045A8 -> 0x08001708, and the log
   append 0x080017D0 (per SERVO_PERSIST_FINDING) -- re-derive them here.
"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from zf_img import Img, load_pair


def imm_sites(im, val, width=(16, 32)):
    """sites where a mov/movw/movs/add/sub/cmp uses `val` as a plain immediate."""
    out = []
    for i in im.index():
        if not i.op_str.startswith('#') and '#' not in i.op_str:
            continue
        for op in i.operands:
            if op.type == 2 and op.imm == val:   # ARM_OP_IMM == 2
                out.append(i)
                break
    return out


def lit_sites(im, val):
    """all 4-aligned or 2-aligned occurrences of `val` in the image + who loads them."""
    res = []
    for o in range(0, len(im.blob) - 4, 4):
        if struct.unpack_from('<I', im.blob, o)[0] == val:
            res.append(im.base + o)
    return res


def main():
    a, b = load_pair()
    print('### A. positive self-check on immediate scanning')
    for im in (a, b):
        print('  %s  movw #0x4E20 (20000) sites: %s' %
              (im.name, ['0x%08x' % i.address for i in imm_sites(im, 20000) if i.mnemonic == 'movw']))
    for im in (a, b):
        for v in (0x45670123, 0xCDEF89AB, 0xBE6D4A8B, 0xA1B2C3D4,
                  0x2001, 0x200C, 0x2000, 0x20010C):
            ls = lit_sites(im, v)
            print('  %-7s lit dword 0x%08x : %d sites %s' %
                  (im.name, v, len(ls), ['0x%08x' % x for x in ls[:8]]))
    print()
    print('### B. vendor param index as *immediate* (any instruction)')
    for im in (a, b):
        for v in (0x2001, 0x200C, 0x2002, 0x2000):
            ss = imm_sites(im, v)
            print('  %-7s imm 0x%04x : %d sites %s' %
                  (im.name, v, len(ss), ['%08x/%s' % (i.address, i.mnemonic) for i in ss[:10]]))
        for v in (38, 189, 39):
            ss = imm_sites(im, v)
            print('  %-7s imm %-4d : %d sites' % (im.name, v, len(ss)))
    print()
    print('### C. persistence API chain (per SERVO_PERSIST_FINDING)')
    for im in (a, b):
        # find the magic then look back for the function that writes it
        for magic in (0xBE6D4A8B, 0xA1B2C3D4):
            ls = lit_sites(im, magic)
            print('  %-7s magic 0x%08x at %s' %
                  (im.name, magic, ['0x%08x' % x for x in ls]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
