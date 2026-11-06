"""servo_region_map.py - map the inline-descriptor region 0x08051300..0x08052800 of
the 3.2.D.8 servo image, which SERVO_FW_OD_FINDING.md section 4.1/7.1 identified as
containing the only 6 dwords that point into the OD metadata table.

The note calls it "code + literal mixed".  This script tests that by walking the
region and classifying every 2-byte halfword as "decodes to a plausible Thumb
instruction" vs "does not", then prints the region as a block map plus a table of
the flash-pointer dwords found inside it.

usage:
  python tools\\servo_region_map.py <flash.bin> [--lo 0x08051300] [--hi 0x08052800]
  python tools\\servo_region_map.py <flash.bin> --ptrs
"""
import sys, struct

FLASH_BASE = 0x08000000
OD_LO, OD_HI = 0x08024bd0, 0x0802642e      # real OD entry span (first..last name)


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
    lo = int(argv[argv.index('--lo') + 1], 16) if '--lo' in argv else 0x08051300
    hi = int(argv[argv.index('--hi') + 1], 16) if '--hi' in argv else 0x08052800
    print("region 0x%08x..0x%08x (%d B)" % (lo, hi, hi - lo))

    # --- 1. every dword in the image that points into the OD entry span ---
    print("\n=== dwords pointing into the OD entry span 0x%08x..0x%08x ===" % (OD_LO, OD_HI))
    ptrs = []
    for o in range(0, len(flash) - 4, 2):
        v = struct.unpack_from('<I', flash, o)[0]
        if OD_LO <= v < OD_HI:
            ptrs.append((FLASH_BASE + o, v))
    print("  %d site(s) (2-byte scan)" % len(ptrs))
    for a, v in ptrs:
        inside = "in-region" if lo <= a < hi else "ELSEWHERE"
        print("    0x%08x -> 0x%08x  (%s)" % (a, v, inside))

    # --- 2. walk the region, classify halfwords, and record where the walk desyncs ---
    print("\n=== Thumb walk of the region (desync points) ===")
    o = lo
    runs = []
    cur_start = None
    while o < hi:
        ins = list(md.disasm(flash[o - FLASH_BASE:o - FLASH_BASE + 4], o))
        good = bool(ins)
        if not good and cur_start is None:
            cur_start = o
        if good and cur_start is not None:
            runs.append((cur_start, o))
            cur_start = None
        o += 2
    if cur_start is not None:
        runs.append((cur_start, hi))
    print("  %d non-decodable run(s)" % len(runs))
    for a, b in runs:
        print("     0x%08x..0x%08x (%d B)" % (a, b, b - a))

    # --- 3. block map: for each 32 B, is it code-like? ---
    print("\n=== block map (32 B blocks; C=thumb-decodable, .=not) ===")
    line = []
    for a in range(lo, hi, 32):
        n_ok = 0
        for k in range(0, 32, 2):
            if list(md.disasm(flash[a - FLASH_BASE + k:a - FLASH_BASE + k + 4], a + k)):
                n_ok += 1
        line.append('C' if n_ok >= 15 else ('c' if n_ok >= 8 else '.'))
    for i in range(0, len(line), 64):
        print("  0x%08x  %s" % (lo + i * 32, ''.join(line[i:i + 64])))

    # --- 4. flash-pointer dwords inside the region ---
    print("\n=== dwords inside the region that look like flash pointers (0x0802xxxx / 0x0805xxxx) ===")
    for o2 in range(lo, hi - 4, 4):
        v = struct.unpack_from('<I', flash, o2 - FLASH_BASE)[0]
        if 0x08020000 <= v < 0x08060000:
            note = ""
            if OD_LO <= v < OD_HI:
                note = "  <-- points into OD table"
            print("    0x%08x : 0x%08x%s" % (o2, v, note))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
