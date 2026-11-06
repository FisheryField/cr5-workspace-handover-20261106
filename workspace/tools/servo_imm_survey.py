"""servo_imm_survey.py - survey Thumb instruction immediates by frequency.

Reason for existing: scanning raw bytes for a 16-bit value keeps producing FALSE
POSITIVES in this firmware, because instruction bytes are indistinguishable from data
at that granularity.  Two confirmed instances in this investigation:
    * 0x0804C8C0 read as 0x6064   -> really `ldr r2,[pc,#0x44] ; subs r4,r0,#0`
    * 0x0803D406 read as 2020     -> really `ldrsb r0,[r0,#...]`-class code bytes
So constants must be looked for as INSTRUCTION IMMEDIATES (via capstone), never as
raw bytes.

This script decodes the image with capstone and reports the immediate operands that
actually appear in instructions, grouped by value - which is how a scale factor used
by the position computation would really show up.

usage:
  python tools\\servo_imm_survey.py <flash.bin> [--want 2020] [--top 40] [--min 64]
"""
import sys
import struct
import collections

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
    top = int(argv[argv.index('--top') + 1]) if '--top' in argv else 40
    minsites = int(argv[argv.index('--min') + 1]) if '--min' in argv else 4
    want = int(argv[argv.index('--want') + 1], 0) if '--want' in argv else None

    counts = collections.Counter()
    sites = collections.defaultdict(list)

    a = FLASH_BASE
    n = len(flash)
    while a <= FLASH_BASE + n - 4:
        for i in md.disasm(flash[a - FLASH_BASE:a - FLASH_BASE + 4], a):
            ops = i.op_str
            if '#' in ops:
                # take each immediate operand in the operand string
                for tok in ops.replace(']', ' ').replace('[', ' ').split(','):
                    tok = tok.strip()
                    if tok.startswith('#'):
                        try:
                            v = int(tok[1:], 0)
                        except ValueError:
                            continue
                        counts[v] += 1
                        if len(sites[v]) < 12:
                            sites[v].append((i.address, i.mnemonic, ops))
            break
        a += 2

    print("image %s : %d distinct immediate values" % (path, len(counts)))

    if want is not None:
        print("\n=== occurrences of immediate %d (0x%x) ===" % (want, want))
        if want in counts:
            print("  %d site(s)" % counts[want])
            for s in sites[want]:
                print("    0x%08x  %-9s %s" % s)
        else:
            print("  NOT PRESENT as an instruction immediate")

    print("\n=== most frequent immediates (>= %d sites) ===" % minsites)
    for v, c in counts.most_common(top):
        if c < minsites:
            break
        print("  %-8d (0x%-6x) : %d" % (v, v, c))

    print("\n=== immediates in the 'scale factor' neighbourhood 1000..3000 ===")
    for v in sorted(counts):
        if 1000 <= v <= 3000:
            print("  %-8d (0x%-6x) : %d   e.g. %s" %
                  (v, v, counts[v],
                   '; '.join('0x%x %s %s' % s for s in sites[v][:2])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
