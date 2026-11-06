"""servo_align.py - align two servo firmware flash images (there is a ~9 KB
insertion, so a plain byte-by-byte compare is meaningless) and report the real
functional differences.

usage: python tools\\servo_align.py <new.bin> <old.bin> [--min N] [--max R]
"""
import sys, os, struct, difflib, hashlib, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS, CS_MODE_LITTLE_ENDIAN

FLASH_BASE = 0x08000000
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS | CS_MODE_LITTLE_ENDIAN)

# compare in 4-byte units: instructions stay aligned, so opcode-level matches
# survive register/constant renumbering better than byte-level ones
UNIT = 4


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def words(blob):
    n = len(blob) // UNIT
    return [blob[i * UNIT:(i + 1) * UNIT] for i in range(n)]


def dis(flash, addr, nins):
    off = addr - FLASH_BASE
    out, c = [], 0
    for ins in md.disasm(flash[off:off + nins * 4], addr):
        out.append("  0x%08x  %-31s %-8s %s" %
                   (ins.address, flash[ins.address - FLASH_BASE:ins.address - FLASH_BASE + ins.size].hex(' '),
                    ins.mnemonic, ins.op_str))
        c += 1
        if c >= nins:
            break
    return out


def main(argv):
    new_p, old_p = argv[0], argv[1]
    minrun = int(argv[argv.index('--min') + 1]) if '--min' in argv else 16
    dn, bn, fn = load(new_p)
    do, bo, fo = load(old_p)
    print("new %s  flash %d B  md5 %s" % (os.path.basename(new_p), len(fn), hashlib.md5(dn).hexdigest()))
    print("old %s  flash %d B  md5 %s" % (os.path.basename(old_p), len(fo), hashlib.md5(do).hexdigest()))

    wn, wo = words(fn), words(fo)
    print("comparing %d vs %d four-byte units" % (len(wn), len(wo)))
    sm = difflib.SequenceMatcher(None, wo, wn, autojunk=False)
    ops = sm.get_opcodes()
    ratio = sm.ratio()
    print("similarity ratio: %.4f" % ratio)
    counts = collections.Counter(op[0] for op in ops)
    print("opcodes: %s" % dict(counts))
    print()

    matched_new = sum(op[4] - op[3] for op in ops if op[0] == 'equal')
    matched_old = sum(op[2] - op[1] for op in ops if op[0] == 'equal')
    print("identical 4-byte units: new %d / %d (%.1f%%), old %d / %d (%.1f%%)" %
          (matched_new, len(wn), 100.0 * matched_new / len(wn),
           matched_old, len(wo), 100.0 * matched_old / len(wo)))
    print()
    print("=== structural changes (equal/replace/insert/delete runs) ===")
    for tag, i1, i2, j1, j2 in ops:
        if tag == 'equal':
            continue
        if (i2 - i1) < minrun and (j2 - j1) < minrun:
            continue
        print("  %-8s old 0x%08x..0x%08x (%4d B)  ->  new 0x%08x..0x%08x (%4d B)" %
              (tag, FLASH_BASE + i1 * UNIT, FLASH_BASE + i2 * UNIT, (i2 - i1) * UNIT,
               FLASH_BASE + j1 * UNIT, FLASH_BASE + j2 * UNIT, (j2 - j1) * UNIT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
