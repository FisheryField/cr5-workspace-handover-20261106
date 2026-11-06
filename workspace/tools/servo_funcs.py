"""servo_funcs.py - build a function-boundary map of a Cortex-M flash image with
capstone (Ghidra's auto analysis only found 10 functions because it never
followed the vector table / BL targets through a flat binary).

Method:
  * linear-disassemble the whole .text once, collecting
      - BL / BLX direct targets            -> function starts
      - vector table entries               -> function starts
      - `ldr rX,[pc,#n]` literal words that point into .text (odd = Thumb)
  * then walk the sorted starts and record each function's extent up to the
    next start.

usage:
  python tools\\servo_funcs.py <firmware.bin> [--json out.json] [--list N]
"""
import sys, os, struct, json, hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS, CS_MODE_LITTLE_ENDIAN

FLASH_BASE = 0x08000000
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS | CS_MODE_LITTLE_ENDIAN)
md.detail = True


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def in_flash(a, size):
    return FLASH_BASE <= a < FLASH_BASE + size


def scan(flash):
    size = len(flash)
    starts = set()
    bl_targets = []
    lit_targets = []

    # vector table (first 0x100 bytes) - entries 1..15 are handlers
    for i in range(1, 16):
        v = struct.unpack_from('<I', flash, i * 4)[0]
        if v and in_flash(v & ~1, size):
            starts.add(v & ~1)

    md.skipdata = True
    for ins in md.disasm(flash, FLASH_BASE):
        m, s = ins.mnemonic, ins.op_str
        if m in ('bl', 'blx') and s.startswith('#') and not s.startswith('#0x'):
            pass
        if m in ('bl', 'blx'):
            tgt = None
            if s.startswith('#'):
                try:
                    tgt = int(s[1:], 0)
                except ValueError:
                    tgt = None
            if tgt and in_flash(tgt & ~1, size):
                starts.add(tgt & ~1)
                bl_targets.append(tgt & ~1)
        if m == 'ldr' and '[pc' in s:
            try:
                import re
                imm = int(re.search(r'#(-?0x[0-9a-fA-F]+|-?\d+)', s).group(1), 0)
            except Exception:
                continue
            pc = (ins.address + 4) & ~1
            lit = pc + imm
            off = lit - FLASH_BASE
            if 0 <= off <= size - 4:
                w = struct.unpack_from('<I', flash, off)[0]
                if in_flash(w & ~1, size) and (w & 1):
                    starts.add(w & ~1)
                    lit_targets.append(w & ~1)

    starts.add(struct.unpack_from('<I', flash, 4)[0] & ~1)   # Reset
    return sorted(s for s in starts if in_flash(s, size)), len(bl_targets), len(lit_targets)


def main(argv):
    path = argv[0]
    _d, hdr, flash = load(path)
    starts, nbl, nlit = scan(flash)
    print("%s  flash %d B  md5 %s" % (os.path.basename(path), len(flash), hashlib.md5(flash).hexdigest()))
    print("  function starts: %d   (from %d BL targets, %d literal-pool pointers)" %
          (len(starts), nbl, nlit))
    sizes = [b - a for a, b in zip(starts, starts[1:])]
    if sizes:
        print("  function size: min %d median %d max %d" % (min(sizes), sorted(sizes)[len(sizes) // 2], max(sizes)))
    if '--list' in argv:
        n = int(argv[argv.index('--list') + 1])
        for a, b in list(zip(starts, starts[1:]))[:n]:
            print("   0x%08x  (%d B)" % (a, b - a))
    if '--json' in argv:
        out = argv[argv.index('--json') + 1]
        json.dump({"flash_md5": hashlib.md5(flash).hexdigest(), "size": len(flash),
                   "starts": starts}, open(out, 'w'))
        print("  wrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
