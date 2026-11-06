"""DEPRECATED / DEFECTIVE - do NOT trust its negative results.

This detector SILENTLY RETURNED ZERO HITS for accesses that are plainly visible in
the disassembly, because of three compounding bugs:
  1. its mnemonic table lacked the wide forms (ldrh.w / strh.w / ldrsh.w ...) which
     this firmware uses almost exclusively,
  2. its backward scan walked over unrelated instructions and broke on the first miss,
  3. it required an instruction adjacency the compiler does not guarantee.

Use tools/servo_field_refs.py instead (forward abstract interpretation + one-step
dereference propagation).  Self-check: *(0x200016B5)+0xB8 goes 0 -> 7 sites,
+0xBA goes 0 -> 3 sites.

Kept only so the record of the mistake survives.
"""
"""servo_find_field.py - find reads and writes of ONE struct field, given the struct's
base-pointer global and the field offset.

Need: the one-shot position-command re-init in 3.2.D.8 is triggered by the 16-bit flag
[0x200016B5 + 0xB8].  To find the door into the calibration/homing path we must find
who SETS that flag, and who reads it.

Naive literal scanning does not work here: code loads the base pointer from a literal
(`ldr rX,[pc]` = 0x200016B5), dereferences it, and only then does an offset access.  So
this script does an instruction-level dataflow-lite match:

    ldr  rB, [pc, ...]        ; literal == BASE
    ...  (0..6 insns)
    ldr  rS, [rB]             ; rS = *BASE        (skip if the literal is not a ptr)
    ...  (0..6 insns)
    ldr  / ldrh / str / strh  rd, [rS, #OFF]

and also the simpler direct form where a literal holds BASE+OFF.

usage:
  python tools\\servo_find_field.py <flash.bin> --base 0x200016b5 --off 0xb8
  python tools\\servo_find_field.py <flash.bin> --base 0x200016b5 --off 0xb8 --compare <other.bin>
"""
import sys, struct

FLASH_BASE = 0x08000000
MN_LD = ('ldr', 'ldrh', 'ldrb', 'ldrsb', 'ldrsh')
MN_ST = ('str', 'strh', 'strb')


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def find(md, flash, BASE, OFF):
    """Return list of (addr, mnemonic, op_str, kind) for accesses to BASE->+OFF."""
    insns = {}
    a = FLASH_BASE
    n = len(flash)
    while a <= FLASH_BASE + n - 4:
        for i in md.disasm(flash[a - FLASH_BASE:a - FLASH_BASE + 4], a):
            insns[a] = (i.mnemonic, i.op_str)
            break
        a += 2
    order = sorted(insns)

    def lit_of(addr):
        mn, ops = insns.get(addr, (None, ''))
        if mn != 'ldr' or 'pc' not in ops:
            return None
        try:
            off = int(ops.split('#')[-1].rstrip(']'), 0)
        except ValueError:
            return None
        tgt = ((addr + 4) & ~3) + off
        if FLASH_BASE <= tgt <= FLASH_BASE + len(flash) - 4:
            return struct.unpack_from('<I', flash, tgt - FLASH_BASE)[0]
        return None

    hits = []
    for a in order:
        mn, ops = insns[a]
        if not mn.startswith(MN_LD + MN_ST) or '[' not in ops:
            continue
        inside = ops[ops.index('[') + 1:ops.index(']') if ']' in ops else len(ops)]
        parts = [p.strip() for p in inside.split(',')]
        if len(parts) < 2:
            continue
        reg, offs = parts[0], parts[1]
        if not offs.startswith('#0x'):
            continue
        try:
            off = int(offs[1:], 16)
        except ValueError:
            continue
        if off != OFF:
            continue
        # walk back: find how `reg` was set up
        for back in range(2, 24, 2):
            pa = a - back
            if pa not in insns:
                continue
            pmn, pops = insns[pa]
            # form A: ldr reg,[other]  where other came from literal BASE
            if pmn == 'ldr' and pops.startswith(reg + ',') and '[' in pops:
                src = pops[pops.index('[') + 1:pops.index(']')].split(',')[0].strip()
                for back2 in range(2, 16, 2):
                    pb = pa - back2
                    if lit_of(pb) == BASE:
                        pmn2, pops2 = insns[pb]
                        if pops2.startswith(src + ','):
                            kind = 'write' if mn in MN_ST else 'read'
                            hits.append((a, mn, ops, kind + ' (via *BASE)'))
                            break
                break
            # form B: reg = BASE + OFF directly
            if pmn in ('add', 'adds', 'add.w') and pops.startswith(reg + ','):
                base_reg = pops.split(',')[1].strip()
                try:
                    imm = int(pops.split('#')[-1], 0)
                except ValueError:
                    imm = None
                if imm == OFF:
                    for back2 in range(2, 16, 2):
                        if lit_of(a - back2 - back) == BASE or lit_of(a - back - back2) == BASE:
                            kind = 'write' if mn in MN_ST else 'read'
                            hits.append((a, mn, ops, kind + ' (BASE+off)'))
                            break
                    break
            if pmn == 'ldr' and pops.startswith(reg + ',') and 'pc' in pops:
                if lit_of(pa) == BASE + OFF:
                    kind = 'write' if mn in MN_ST else 'read'
                    hits.append((a, mn, ops, kind + ' (literal BASE+off)'))
                break
    # dedupe
    seen, out = set(), []
    for h in hits:
        if h[0] in seen:
            continue
        seen.add(h[0])
        out.append(h)
    return out


def main(argv):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    BASE = int(argv[argv.index('--base') + 1], 16)
    OFF = int(argv[argv.index('--off') + 1], 16)

    flash = load(argv[0])[2]
    print("target: *(0x%08x) + 0x%02x     in %s" % (BASE, OFF, argv[0]))
    hits = find(md, flash, BASE, OFF)
    print("  %d access site(s)" % len(hits))
    for a, mn, ops, kind in hits:
        print("    0x%08x  %-8s %-28s %s" % (a, mn, ops, kind))

    if '--compare' in argv:
        other = argv[argv.index('--compare') + 1]
        f2 = load(other)[2]
        h2 = find(md, f2, BASE, OFF)
        print("\n  %s : %d access site(s)" % (other, len(h2)))
        for a, mn, ops, kind in h2:
            print("    0x%08x  %-8s %-28s %s" % (a, mn, ops, kind))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
