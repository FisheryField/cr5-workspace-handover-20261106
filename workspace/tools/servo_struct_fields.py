"""servo_struct_fields.py - for a pointer global, classify every load site by WHICH FIELD
of the pointed-to struct it touches.

Why: 0x20003DB0 is now known to be a struct with
    +0x00 position      +0x04 quotient (turns)     +0x08 remainder A
    +0x0C remainder B   +0x10 selector (0/1)
but its CONSUMERS are unknown, and finding them by reading 79 raw reference sites by hand
is impractical.  This script does the classification mechanically:

  * find every `ldr rX,[pc,#n]` whose literal VALUE == the target pointer
  * then look ahead a few instructions for accesses of the form
        ldr/ldrh/str/strh ... [rX, #off]
    (also handling the case where rX is re-loaded via a second literal hop)
  * aggregate by offset, with read/write kind, so the struct's usage profile appears

usage:
  python tools\\servo_struct_fields.py <flash.bin> --ptr 0x20003db0
  python tools\\servo_struct_fields.py <flash.bin> --ptr 0x20003db0 --compare <other.bin>
  python tools\\servo_struct_fields.py <flash.bin> --ptr 0x20003db0 --off 0x10 --list
"""
import sys, struct
from collections import Counter, defaultdict

FLASH_BASE = 0x08000000
LD = ('ldr', 'ldrh', 'ldrb', 'ldrsb', 'ldrsh', 'ldrd',
      # FP/vector loads - these were MISSING, which made every float field access
      # invisible to this tool (e.g. vldr s0,[r0,#0x10] never appeared in a table).
      'vldr', 'vldrh', 'vldm')
ST = ('str', 'strh', 'strb', 'strd', 'vstr', 'vstrh', 'vstm')


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def norm(mn):
    return mn[:-2] if mn.endswith('.w') else mn


def analyse(md, flash, PTR, lookahead=10):
    """Return list of (site, reg, field_off, kind, mnemonic, op_str)."""
    n = len(flash)
    out = []
    a = FLASH_BASE
    while a <= FLASH_BASE + n - 4:
        ins = list(md.disasm(flash[a - FLASH_BASE:a - FLASH_BASE + 4], a))
        if not ins:
            a += 2
            continue
        i = ins[0]
        if norm(i.mnemonic) == 'ldr' and 'pc' in i.op_str:
            try:
                off = int(i.op_str.split('#')[-1].rstrip(']'), 0)
                tgt = ((i.address + 4) & ~3) + off
                val = struct.unpack_from('<I', flash, tgt - FLASH_BASE)[0] if \
                    FLASH_BASE <= tgt <= FLASH_BASE + n - 4 else None
            except (ValueError, IndexError):
                val = None
            if val == PTR:
                reg = i.op_str.split(',')[0].strip()
                # look ahead for [reg, #off]
                p = i.address + i.size
                seen = 0
                for k in md.disasm(flash[p - FLASH_BASE:p - FLASH_BASE + 4 * lookahead], p):
                    seen += 1
                    ops = k.op_str
                    mn = norm(k.mnemonic)
                    if mn in LD + ST and ('[' + reg + ',') in ops.replace(' ', '') or \
                       (mn in LD + ST and ops.replace(' ', '').startswith(reg and '')):
                        pass
                    if mn in LD + ST and '[' in ops:
                        body = ops[ops.index('[') + 1:].split(']')[0]
                        parts = [x.strip() for x in body.split(',')]
                        if parts[0] == reg:
                            fo = 0
                            if len(parts) > 1 and parts[1].startswith('#'):
                                try:
                                    fo = int(parts[1][1:], 0)
                                except ValueError:
                                    fo = 0
                            kind = 'W' if mn in ST else 'R'
                            out.append((i.address, reg, fo, kind, k.mnemonic, k.op_str))
                    # if reg is overwritten, stop
                    fl = ops.split(',')[0].strip() if ops else ''
                    if fl == reg and mn not in LD + ST:
                        break
                    # CRITICAL: a later `ldr rX,[pc]` re-loads the SAME register, so any
                    # access after it belongs to THAT value, not to ours.  Not stopping
                    # here makes the same access get attributed to every earlier load,
                    # which inflated the field histogram and produced a phantom
                    # "+0x08/+0x0C are symmetric duplicates" reading.
                    if mn == 'ldr' and 'pc' in ops and fl == reg:
                        break
                    if k.mnemonic.startswith('pop'):
                        break
        a += i.size
    return out


def report(path, hits, PTR):
    print("### %s   pointer 0x%08X" % (path, PTR))
    per = defaultdict(Counter)
    sites = defaultdict(list)
    for site, reg, fo, kind, mn, ops in hits:
        per[fo][kind] += 1
        sites[fo].append((site, mn, ops, kind))
    print("  %-8s %-6s %-6s" % ("offset", "reads", "writes"))
    for fo in sorted(per):
        print("  +0x%02X    %-6d %-6d" % (fo, per[fo]['R'], per[fo]['W']))
    return sites


def main(argv):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    PTR = int(argv[argv.index('--ptr') + 1], 16)

    flash = load(argv[0])[2]
    hits = analyse(md, flash, PTR)
    sites = report(argv[0], hits, PTR)

    if '--off' in argv:
        fo = int(argv[argv.index('--off') + 1], 16)
        only = None
        if '--only' in argv:
            only = argv[argv.index('--only') + 1].upper()   # R or W
        print("\n=== sites touching +0x%02X%s ===" %
              (fo, '' if only is None else ' (kind=%s)' % only))
        rows = sorted(sites.get(fo, []))
        shown = 0
        for site, mn, ops, kind in rows:
            if only and kind != only:
                continue
            print("  0x%08x  %-9s %-28s %s" % (site, mn, ops, kind))
            shown += 1
        if shown == 0:
            print("  (none)")
        else:
            print("  %d site(s)" % shown)

    if '--compare' in argv:
        other = argv[argv.index('--compare') + 1]
        f2 = load(other)[2]
        h2 = analyse(md, f2, PTR)
        print()
        report(other, h2, PTR)
        per_a = Counter(fo for _s, _r, fo, _k, _m, _o in hits)
        per_b = Counter(fo for _s, _r, fo, _k, _m, _o in h2)
        print("\n  offsets only in A: %s" % sorted(set(per_a) - set(per_b)))
        print("  offsets only in B: %s" % sorted(set(per_b) - set(per_a)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
