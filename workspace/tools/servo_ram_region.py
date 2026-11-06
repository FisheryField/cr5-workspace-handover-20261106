"""servo_ram_region.py - report every reference to a RAM address in the servo image.

Context: the non-volatile save routine at 0x080017d0 of firmware 3.2.D.8 reads a
16-byte payload from RAM address 0x200096E8 and appends it to a flash log at
0x0800C000.  To understand WHAT is persisted (and whether it can be the zero
offset), we need every place that touches that RAM region.

This script finds, for a given RAM address (or range):
  * literal-pool dwords holding the address or a nearby one (same struct)
  * `movw/movt` immediate pairs producing it
  * ldr/str sites whose resolved literal points into the region

usage:
  python tools\\servo_ram_region.py <flash.bin> --at 0x200096e8 [--window 0x40]
  python tools\\servo_ram_region.py <flash.bin> --at 0x20003470
"""
import sys, struct

FLASH_BASE = 0x08000000


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def main(argv):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)

    path = argv[0]
    flash, _b, _f = load(path)
    target = int(argv[argv.index('--at') + 1], 16)
    win = int(argv[argv.index('--window') + 1], 16) if '--window' in argv else 0x40
    lo, hi = target, target + win
    print("target RAM region 0x%08x..0x%08x (window 0x%x)" % (lo, hi, win))

    # 1. map every ldr rX,[pc,#n] to its literal target, then flag the RAM range
    print("\n=== PC-relative literal loads pointing into the region ===")
    hits = []
    for a in range(FLASH_BASE, FLASH_BASE + len(flash) - 4, 2):
        for i in md.disasm(flash[a - FLASH_BASE:a - FLASH_BASE + 4], a):
            if i.mnemonic == 'ldr' and 'pc' in i.op_str:
                try:
                    off = int(i.op_str.split('#')[-1].rstrip(']'), 0)
                except ValueError:
                    break
                tgt = ((i.address + 4) & ~3) + off
                if FLASH_BASE <= tgt <= FLASH_BASE + len(flash) - 4:
                    v = struct.unpack_from('<I', flash, tgt - FLASH_BASE)[0]
                    if lo <= v < hi:
                        # find the companion ldr/str that dereferences it
                        nxt = []
                        for j in md.disasm(flash[i.address - FLASH_BASE + 4:
                                                i.address - FLASH_BASE + 16],
                                           i.address + 4):
                            nxt.append("%s %s" % (j.mnemonic, j.op_str))
                        hits.append((i.address, tgt, v, nxt))
            break
    seen = set()
    for a, tgt, v, nxt in hits:
        key = (a, v)
        if key in seen:
            continue
        seen.add(key)
        print("  0x%08x  ldr [pc]->0x%08x = 0x%08x   then: %s" %
              (a, tgt, v, ' ; '.join(nxt[:3])))
    print("  %d distinct site(s)" % len(seen))

    # 2. raw dwords in the image equal to the target
    print("\n=== raw dwords equal to 0x%08x ===" % target)
    n = 0
    for o in range(0, len(flash) - 4, 4):
        if struct.unpack_from('<I', flash, o)[0] == target:
            print("    0x%08x" % (FLASH_BASE + o))
            n += 1
    print("  %d site(s)" % n)

    # 3. show the literals' neighbourhood so struct layout is visible
    if hits:
        print("\n=== literal-pool neighbourhoods ===")
        for tgt in sorted({t for _a, t, _v, _n in hits}):
            print("  pool around 0x%08x:" % tgt)
            base = tgt - 0x20
            for o in range(base, tgt + 0x40, 4):
                if FLASH_BASE <= o < FLASH_BASE + len(flash) - 4:
                    v = struct.unpack_from('<I', flash, o - FLASH_BASE)[0]
                    tag = ""
                    if 0x20000000 <= v < 0x20050000:
                        tag = "  RAM"
                    elif 0x08000000 <= v < 0x08060000:
                        tag = "  FLASH"
                    star = " <=" if o == tgt else ""
                    print("    0x%08x = 0x%08x%s%s" % (o, v, tag, star))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
