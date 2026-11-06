"""servo_ptr_array.py - characterise a suspected 4-byte-stride pointer array in the
servo image, including finding its true alignment.

tools/servo_region_map.py found that the region 0x08051300..0x08052800 holds a run of
dwords that look like flash pointers but appear misaligned (every 4th byte is 0x08).
That is the signature of a 4-byte array whose start is offset by 1..3 bytes - in an
ARM image the array start is normally 4-byte aligned, so re-deriving the alignment
tells us where the array really begins.

This script:
  1. scores each of the 4 alignments by the fraction of entries that land in a
     plausible flash address range
  2. reports the best alignment and prints the array with resolved targets
  3. for each target, reports whether it decodes as a plausible function prologue

usage:
  python tools\\servo_ptr_array.py <flash.bin> --around 0x08051bc0
  python tools\\servo_ptr_array.py <flash.bin> --lo 0x08051b00 --hi 0x08051d00
"""
import sys, struct

FLASH_BASE = 0x08000000
# plausible flash target range for this image (code + rodata, excluding the
# appended 0x08xxxxxx regions)
TLO, THI = 0x08000000, 0x08052900


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def score(flash, start, n):
    good = 0
    for i in range(n):
        o = start - FLASH_BASE + 4 * i
        if o < 0 or o + 4 > len(flash):
            return good, i
        v = struct.unpack_from('<I', flash, o)[0]
        if TLO <= (v & ~1) < THI:
            good += 1
    return good, n


def main(argv):
    path = argv[0]
    flash, _b, _f = load(path)

    if '--around' in argv:
        c = int(argv[argv.index('--around') + 1], 16)
        base = c - 0x40
        span = 0x100
    else:
        base = int(argv[argv.index('--lo') + 1], 16)
        span = int(argv[argv.index('--hi') + 1], 16) - base

    print("scan window 0x%08x (+%d B)" % (base, span))
    print("\n=== alignment scoring (fraction of entries in 0x%08x..0x%08x) ===" % (TLO, THI))
    best = None
    for off in range(4):
        g, n = score(flash, base + off, span // 4)
        pct = 100.0 * g / max(1, n)
        print("  start 0x%08x : %d/%d = %.1f%%" % (base + off, g, n, pct))
        if best is None or pct > best[2]:
            best = (base + off, g, pct, n)
    print("  => best alignment: 0x%08x (%.1f%%)" % (best[0], best[2]))

    st = best[0]
    print("\n=== array at 0x%08x ===" % st)
    for i in range(span // 4):
        o = st - FLASH_BASE + 4 * i
        if o < 0 or o + 4 > len(flash):
            break
        v = struct.unpack_from('<I', flash, o)[0]
        ok = TLO <= (v & ~1) < THI
        pro = ""
        if ok:
            # a plausible Thumb function prologue: push {..,lr} / sub sp / mov
            b = flash[(v & ~1) - FLASH_BASE:(v & ~1) - FLASH_BASE + 4]
            if len(b) >= 2 and b[1] == 0xB5:
                pro = "  push{...,lr}"
            elif len(b) >= 4 and b[2] == 0xB0:
                pro = "  sub sp"
        print("  [%3d] 0x%08x -> 0x%08x %s%s" % (i, st + 4 * i, v, "OK" if ok else "out-of-range", pro))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
