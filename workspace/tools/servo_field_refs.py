"""servo_field_refs.py - robust finder for EVERY access to one struct field
`(*(BASE)) + OFF`, i.e. the field lives in a struct reached through a pointer global.

Why a rewrite was needed
------------------------
The previous attempt (tools/servo_find_field.py) returned ZERO hits even for accesses
visible by hand, because of three compounding bugs:
  1. its mnemonic table lacked the wide forms (`ldrh.w`, `strh.w`, ...), and
  2. its backward scan scanned over unrelated instructions and `break`ed on the first
     miss, and
  3. it required a specific instruction adjacency that the compiler does not guarantee.
A detector that silently reports "0 references" for something known to exist is worse
than no detector, so this version does a **forward abstract interpretation** instead:

    * walk instructions in address order
    * track, per register, whether it currently holds a known constant
      (from `ldr rX,[pc,#n]` literal pools and `movw/movt`), and whether that constant
      is BASE, BASE+OFF, or *BASE
    * at every load/store `[rB, #imm]`, if rB is known and known+imm == BASE+OFF,
      report the site with its kind (read/write) and width
    * invalidate tracked registers on any instruction that writes them in a way we do
      not model (so no stale facts)

usage:
  python tools\\servo_field_refs.py <flash.bin> --base 0x200016b5 --off 0xba
  python tools\\servo_field_refs.py <flash.bin> --base 0x200016b5 --off 0xb8 --compare <other.bin>
  python tools\\servo_field_refs.py <flash.bin> --base 0x200016b5 --offs 0xb8,0xba,0x20
"""
import sys, struct

FLASH_BASE = 0x08000000

LOAD_MN = ('ldr', 'ldrh', 'ldrb', 'ldrsb', 'ldrsh', 'ldrd')
STORE_MN = ('str', 'strh', 'strb', 'strd')
BRANCH_MN = ('b', 'bl', 'bx', 'blx', 'cbz', 'cbnz', 'beq', 'bne', 'bgt', 'blt',
             'bge', 'ble', 'bhi', 'bls', 'bhs', 'blo', 'bcs', 'bcc', 'bmi', 'bpl',
             'tbb', 'tbh')


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def norm_mn(mn):
    return mn[:-2] if mn.endswith('.w') else mn


def regs_written(mn, ops):
    """Best-effort set of registers the instruction writes (destroys tracking)."""
    mn = norm_mn(mn)
    out = set()
    if not ops:
        return out
    first = ops.split(',')[0].strip()
    if first.startswith('r') and first[1:].isdigit():
        out.add(first)
    elif first in ('sb', 'sl', 'fp', 'ip', 'sp', 'lr', 'pc'):
        out.add(first)
    if mn.startswith('pop'):
        out.add('pc')
    return out


def analyse(md, flash, BASE, OFF):
    """Return list of (addr, mnemonic, op_str, kind, width)."""
    hits = []
    n = len(flash)
    facts = {}          # reg -> constant value
    a = FLASH_BASE
    while a <= FLASH_BASE + n - 4:
        ms = list(md.disasm(flash[a - FLASH_BASE:a - FLASH_BASE + 4], a))
        if not ms:
            a += 2
            continue
        i = ms[0]
        mn, ops = norm_mn(i.mnemonic), i.op_str

        # literal pool load: ldr rX,[pc,#n]
        if mn == 'ldr' and 'pc' in ops and '[' in ops:
            try:
                off = int(ops.split('#')[-1].rstrip(']'), 0)
                tgt = ((i.address + 4) & ~3) + off
                if FLASH_BASE <= tgt <= FLASH_BASE + n - 4:
                    val = struct.unpack_from('<I', flash, tgt - FLASH_BASE)[0]
                    dst = ops.split(',')[0].strip()
                    facts[dst] = val
            except (ValueError, IndexError):
                pass
            a += i.size
            continue

        # movw/movt
        if mn in ('movw', 'movt') and '#' in ops:
            try:
                imm = int(ops.split('#')[-1], 0)
                dst = ops.split(',')[0].strip()
                if mn == 'movw':
                    facts[dst] = imm
                elif dst in facts:
                    facts[dst] = (facts[dst] & 0xFFFF) | (imm << 16)
            except (ValueError, IndexError):
                pass
            a += i.size
            continue

        # scaled index: `mul rD, rS, rB` / `muls rD, rS, rB` where rB holds a constant
        # -> rD = rS * const.  Tracked as the marker ('X', const) so that an
        # `add rD, rP, rX` produces ('+', base_ptr, const) and a following
        # `[rD, #imm]` is recognised as *(base_ptr + idx*const + imm).
        if mn in ('mul', 'muls') and ops.count(',') == 2:
            parts = [p.strip() for p in ops.split(',')]
            dst, src, kreg = parts
            if kreg in facts and isinstance(facts[kreg], int):
                facts[dst] = ('X', facts[kreg])          # dst = src * const
            else:
                facts.pop(dst, None)
            a += i.size
            continue

        # `add rD, rP, rX` where rX = idx * const  ->  rD = ptr + idx*const
        if mn in ('add', 'adds', 'add.w') and ops.count(',') == 2:
            parts = [p.strip() for p in ops.split(',')]
            dst, s1, s2 = parts
            if s2 in facts and isinstance(facts[s2], tuple) and facts[s2][0] == 'X' \
               and s1 in facts and isinstance(facts[s1], int):
                facts[dst] = ('+', facts[s1], facts[s2][1])
            else:
                facts.pop(dst, None)
            a += i.size
            continue

        # memory access: [rB, #imm]
        if mn in LOAD_MN + STORE_MN and '[' in ops:
            body = ops[ops.index('[') + 1:]
            body = body.split(']')[0]
            parts = [p.strip() for p in body.split(',')]
            base_reg = parts[0]
            imm = 0
            if len(parts) > 1 and parts[1].startswith('#'):
                try:
                    imm = int(parts[1][1:], 0)
                except ValueError:
                    imm = 0
            # dereference tracking: `ldr rX,[rY]` where rY holds a known pointer.
            # The realistic pattern in this firmware is
            #     ldr  r0,[pc,#n]   ; r0 = BASE  (a pointer variable)
            #     ldr  r0,[r0]      ; r0 = *BASE  (the struct the field lives in)
            #     ldrh r0,[r0,#0xb8]
            # so the effective base for the field access is *BASE, not BASE.  Track it
            # as a distinct marker instead of dropping it (an earlier version dropped it
            # and therefore missed every access written in this very common form).
            if len(parts) == 1:
                dst = ops.split(',')[0].strip()
                if base_reg in facts:
                    facts[dst] = ('*', facts[base_reg])
                else:
                    facts.pop(dst, None)
            if base_reg in facts:
                fv = facts[base_reg]
                star = isinstance(fv, tuple) and fv[0] == '*'
                val = fv[1] if star else fv
                match = False
                note = ''
                if star:
                    # *BASE + OFF
                    match = (val == BASE and imm == OFF)
                    note = 'via *BASE'
                elif isinstance(fv, tuple) and fv[0] == '+':
                    # ptr + idx*stride + OFF  ->  matches *(BASE) + OFF when ptr == BASE
                    match = (fv[1] == BASE and imm == OFF)
                    note = 'via BASE+idx*0x%x' % fv[2]
                elif isinstance(fv, int):
                    # BASE + OFF
                    match = (fv + imm == BASE + OFF)
                    note = 'via BASE'
                if match:
                    width = 1 if 'b' in mn else (2 if 'h' in mn else (8 if mn.endswith('d') else 4))
                    kind = 'write' if mn in STORE_MN else 'read'
                    hits.append((i.address, i.mnemonic, i.op_str, kind, width, note))
            # the access itself does not change the base register
            a += i.size
            continue

        # anything else: destroy tracking for registers it writes
        for r in regs_written(i.mnemonic, ops):
            facts.pop(r, None)
        if i.mnemonic in BRANCH_MN or i.mnemonic.startswith('pop'):
            # conservative: a call/branch may change globals' targets; keep simple facts
            pass
        a += i.size
    return hits


def main(argv):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)

    BASE = int(argv[argv.index('--base') + 1], 16)
    offs = []
    if '--off' in argv:
        offs = [int(argv[argv.index('--off') + 1], 16)]
    elif '--offs' in argv:
        offs = [int(x, 16) for x in argv[argv.index('--offs') + 1].split(',')]

    for OFF in offs:
        flash = load(argv[0])[2]
        hits = analyse(md, flash, BASE, OFF)
        print("### %s   field *(0x%08x) + 0x%02X   -> %d site(s)" %
              (argv[0], BASE, OFF, len(hits)))
        for a, mn, ops, kind, w, note in hits:
            print("    0x%08x  %-9s %-26s %-6s width=%d  %s" % (a, mn, ops, kind, w, note))
        if '--compare' in argv:
            other = argv[argv.index('--compare') + 1]
            f2 = load(other)[2]
            h2 = analyse(md, f2, BASE, OFF)
            print("    %s : %d site(s)" % (other, len(h2)))
            for a, mn, ops, kind, w, note in h2:
                print("    0x%08x  %-9s %-26s %-6s width=%d  %s" % (a, mn, ops, kind, w, note))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
