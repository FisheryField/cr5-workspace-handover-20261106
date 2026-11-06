"""servo_align2.py - align two servo firmware payloads at their *application*
base and report functional differences.

Key point (from the 3.1.5.0 manifest): the two packages do NOT start at the same
flash address.

  * 3.1.5.0 package payload starts at 0x08010000 (application only; the low
    region 0x08000000..0x0800FFFF is not in the package).
  * 3.2.D.8 package payload starts at 0x08000000 and therefore contains the
    64 KiB below 0x08010000 as well.

So the comparison must start at flash 0x08010000 in both, otherwise ~64 KiB of
bootloader is counted as "difference".

usage: python tools\\servo_align2.py <new.bin> <old.bin> [--min N] [--addr HEX]
"""
import sys, os, struct, difflib, hashlib, collections

FLASH_BASE = 0x08000000
APP_BASE = 0x08010000
UNIT = 4


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def words(b):
    return [b[i * UNIT:(i + 1) * UNIT] for i in range(len(b) // UNIT)]


def main(argv):
    new_p, old_p = argv[0], argv[1]
    app_base = int(argv[argv.index('--addr') + 1], 16) if '--addr' in argv else APP_BASE
    minrun = int(argv[argv.index('--min') + 1]) if '--min' in argv else 16

    dn, bn, fn = load(new_p)
    do, bo, fo = load(old_p)
    print("new %-44s payload_start=0x%08x  len=%d" % (os.path.basename(new_p), FLASH_BASE, len(fn)))
    print("old %-44s payload_start=0x%08x  len=%d" % (os.path.basename(old_p), app_base, len(fo)))
    print()

    # slice both from app_base
    n_new = fn[app_base - FLASH_BASE:]
    n_old = fo[app_base - app_base:]      # old payload already starts at app_base
    print("comparing from flash 0x%08x: new %d B vs old %d B (delta %+d)" %
          (app_base, len(n_new), len(n_old), len(n_new) - len(n_old)))

    wn, wo = words(n_new), words(n_old)
    sm = difflib.SequenceMatcher(None, wo, wn, autojunk=False)
    ops = sm.get_opcodes()
    print("similarity ratio: %.4f" % sm.ratio())
    eq_n = sum(o[4] - o[3] for o in ops if o[0] == 'equal')
    eq_o = sum(o[2] - o[1] for o in ops if o[0] == 'equal')
    print("identical 4-byte units: %d / %d (%.1f%%) of new, %d / %d (%.1f%%) of old" %
          (eq_n, len(wn), 100.0 * eq_n / len(wn), eq_o, len(wo), 100.0 * eq_o / len(wo)))
    print("opcodes: %s" % dict(collections.Counter(o[0] for o in ops)))
    print()
    print("=== structural changes >= %d B ===" % minrun)
    tot_i = tot_d = 0
    for tag, i1, i2, j1, j2 in ops:
        if tag == 'equal':
            continue
        if (i2 - i1) < minrun and (j2 - j1) < minrun:
            continue
        if tag == 'insert':
            tot_i += (j2 - j1) * UNIT
        if tag == 'delete':
            tot_d += (i2 - i1) * UNIT
        print("  %-8s old 0x%08x..0x%08x (%5d B) -> new 0x%08x..0x%08x (%5d B)" %
              (tag, app_base + i1 * UNIT, app_base + i2 * UNIT, (i2 - i1) * UNIT,
               app_base + j1 * UNIT, app_base + j2 * UNIT, (j2 - j1) * UNIT))
    print()
    print("inserted in new: %d B ; deleted: %d B" % (tot_i, tot_d))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
