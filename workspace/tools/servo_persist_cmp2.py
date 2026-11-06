"""servo_persist_cmp2.py - compare the non-volatile save routine between the two
servo firmware images, anchored on the magic constant instead of a guessed offset.

tools/servo_flash_hunt.py established that both images contain a full STM32F4
flash HAL (unlock keys 0x45670123 / 0xCDEF89AB, HAL_FLASH_Program, lock).

tools/servo_persist_cmp.py tried to compare the save routines but guessed the
second image's address by a fixed delta and got it wrong.

In fact the magic constant 0xbe6d4a8b is a reliable anchor and sits at a
DIFFERENT address in each image:

    v3.2.D.8   magic @0x08001854   (save routine starts ~0x080017d0)
    v3.1.5.0   magic @0x08001894   (save routine starts ~0x08001810)

so v3.1.5.0's routine is 0x40 LATER, not earlier.  This script:
  1. locates the magic literal in each image
  2. walks back to the enclosing function prologue (push {...lr})
  3. disassembles both with resolved literal pools
  4. diffs the two listings instruction by instruction

usage:
  python tools\\servo_persist_cmp2.py <a.bin> <b.bin>
"""
import sys, struct

FLASH_BASE = 0x08000000
MAGIC = 0xbe6d4a8b


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def dword_sites(flash, val):
    return [FLASH_BASE + o for o in range(0, len(flash) - 4, 2)
            if struct.unpack_from('<I', flash, o)[0] == val]


def listing(flash, lo, ln, md):
    out = []
    for i in md.disasm(flash[lo - FLASH_BASE:lo - FLASH_BASE + ln], lo):
        note = ""
        if i.mnemonic == 'ldr' and 'pc' in i.op_str:
            try:
                off = int(i.op_str.split('#')[-1].rstrip(']'), 0)
                tgt = ((i.address + 4) & ~3) + off
                if FLASH_BASE <= tgt <= FLASH_BASE + len(flash) - 4:
                    note = "= 0x%08x" % struct.unpack_from('<I', flash, tgt - FLASH_BASE)[0]
            except ValueError:
                pass
        if i.mnemonic in ('bl', 'blx') and i.op_str.startswith('#'):
            note = "-> 0x%08x" % (int(i.op_str[1:], 0) & ~1)
        out.append((i.address, i.mnemonic, i.op_str, note))
    return out


def main(argv):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)

    imgs = []
    for path in argv:
        flash, _b, _f = load(path)
        sites = dword_sites(flash, MAGIC)
        print("\n######## %s (%d B) ########" % (path, len(flash)))
        print("  magic 0x%08x literal sites: %s" % (MAGIC, [hex(s) for s in sites]))
        if not sites:
            imgs.append((path, flash, None))
            continue
        mag = sites[0]
        # walk back to the enclosing prologue: push {..,lr} = 0xb5xx high byte
        start = None
        for a in range(mag, max(FLASH_BASE, mag - 0x400), -2):
            o = a - FLASH_BASE
            b = flash[o:o + 2]
            if len(b) == 2 and b[1] == 0xB5:      # push {..., lr}
                start = a
                break
        print("  enclosing save routine starts at %s (magic +0x%x)" %
              (hex(start) if start else "?", mag - start if start else 0))
        imgs.append((path, flash, start))

    print("\n######## side-by-side listings ########")
    lists = []
    for path, flash, start in imgs:
        if start is None:
            lists.append(None)
            continue
        ln = (min(start + 0x180, FLASH_BASE + len(flash))) - start
        L = listing(flash, start, ln, md)
        lists.append(L)
        print("\n---- %s @0x%08x ----" % (path, start))
        for a, m, o, n in L:
            print("  %08x: %-8s %-26s %s" % (a, m, o, n))

    if len(lists) == 2 and all(lists):
        A, B = lists
        print("\n######## instruction-stream comparison ########")
        print("  A has %d insns, B has %d insns" % (len(A), len(B)))
        sa = [(m, o.split('#')[0].strip() if '#' in o else o) for _a, m, o, _n in A]
        sb = [(m, o.split('#')[0].strip() if '#' in o else o) for _a, m, o, _n in B]
        n = min(len(sa), len(sb))
        same = sum(1 for i in range(n) if sa[i] == sb[i])
        print("  identical (mnemonic+shape) at same index: %d / %d (%.1f%%)" %
              (same, n, 100.0 * same / max(1, n)))
        print("\n  first 20 differences:")
        shown = 0
        for i in range(n):
            if sa[i] != sb[i]:
                print("    [%3d] A %08x %-8s %-24s | B %08x %-8s %s" %
                      (i, A[i][0], A[i][1], A[i][2], B[i][0], B[i][1], B[i][2]))
                shown += 1
                if shown >= 20:
                    break
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
