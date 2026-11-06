"""servo_t4_imm.py - T4 helper: find every instruction whose TEXT contains a given
struct-field immediate (e.g. 0x24c = 0x607A descriptor field, 0x238 = 0x6064).

Why this tool (and not servo_field_refs.py)
-------------------------------------------
The field base is  `描述符数组基址 + 轴号*0x329 + off`
(D8 base 0x2000138C / 3150 base 0x2000129C), i.e. a CONSTANT + DYNAMIC INDEX,
which servo_field_refs.py cannot express -> it returns 0 sites (its own docstring says so).
So we fall back to a direct instruction-immediate hunt.

* coordinates: ELF/payload coordinate (payload starts at 0x08000000 in the .elf).
  TRUE flash address = payload address + 0x10000  (payload is loaded at 0x08010000;
  proof: payload word1 = reset vector 0x0801019d).
* MANDATORY positive controls (a silent empty result is the #1 trap here):
    - `movw rX,#0x4e20` (20000) must be found (known site in the position chain)
    - `movw rX,#0x329`  (the per-axis descriptor stride) must be found
  If either is 0 the tool is broken and nothing else may be believed.

usage:
  python tools\\servo_t4_imm.py <payload.bin> --find 0x24c[,0x238,0x230] [--ctx 10]
  python tools\\servo_t4_imm.py <a.bin> --find 0x24c --compare <b.bin> --ctx 8
"""
import sys, struct


def load(path):
    """Return (payload_bytes, payload_base_in_elf_coords=0x08000000)."""
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base
    raise SystemExit("no Cortex-M vector table in %s" % path)


def dis(payload, off, base_off, md, n_insn=None, start_delta=0):
    """Disassemble from off; if n_insn given return that many instructions."""
    out = []
    a = off
    n = len(payload)
    target = start_delta
    while a < n:
        ms = list(md.disasm(payload[a:a + 4], 0x08000000 + (a - base_off)))
        if not ms:
            a += 2
            continue
        i = ms[0]
        out.append((i.address, i.mnemonic, i.op_str))
        if n_insn is not None and len(out) >= n_insn:
            break
        a += i.size
    return out


def all_insn(payload, base_off, md):
    out = []
    a = base_off
    n = len(payload)
    while a <= n - 2:
        ms = list(md.disasm(payload[a:a + 4], 0x08000000 + (a - base_off)))
        if not ms:
            a += 2
            continue
        i = ms[0]
        out.append((a, i.address, i.mnemonic, i.op_str, i.size))
        a += i.size
    return out


def find_imm(insns, imm):
    """Every instruction whose op_str mentions the immediate, in any encoding."""
    forms = ['#0x%x' % imm, '#%d' % imm]
    hits = []
    for k, (off, addr, mn, ops, size) in enumerate(insns):
        for f in forms:
            if f in ops:
                hits.append((k, off, addr, mn, ops))
                break
    return hits


def show(insns, hits, ctx, title):
    print("### %s   -> %d site(s)" % (title, len(hits)))
    for k, off, addr, mn, ops in hits:
        lo = max(0, k - ctx)
        hi = min(len(insns), k + ctx + 1)
        print("  ---- hit @ payload 0x%08x (true 0x%08x)  fileoff 0x%x : %s %s" %
              (addr, addr + 0x10000, off, mn, ops))
        for j in range(lo, hi):
            o, a2, m2, p2, _ = insns[j]
            mark = '>>' if j == k else '  '
            print("   %s 0x%08x (true 0x%08x)  %-9s %s" % (mark, a2, a2 + 0x10000, m2, p2))
    print()


def main(argv):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.detail = False

    path = argv[0]
    payload, base_off = load(path)
    insns = all_insn(payload, base_off, md)
    print("== %s : payload %d B, %d instructions, vector table at file off 0x%x" %
          (path, len(payload), len(insns), base_off))

    # ---- MANDATORY positive controls ----
    ok = True
    for pcv, name in ((0x4e20, 'movw #0x4e20 (20000)'), (0x329, 'movw #0x329 (stride)')):
        h = [x for x in find_imm(insns, pcv) if x[3].startswith('movw')]
        print("   [positive control] %-28s -> %d site(s) %s" %
              (name, len(h), ['0x%08x' % x[2] for x in h[:6]]))
        if not h:
            ok = False
    print("   [positive control] VERDICT: %s" % ("PASS" if ok else "*** FAIL - tool untrustworthy ***"))

    offs = [int(x, 16) for x in argv[argv.index('--find') + 1].split(',')]
    ctx = int(argv[argv.index('--ctx') + 1]) if '--ctx' in argv else 8

    for imm in offs:
        hits = find_imm(insns, imm)
        show(insns, hits, ctx, "%s  imm 0x%x" % (path, imm))
        if '--compare' in argv:
            other = argv[argv.index('--compare') + 1]
            p2, b2 = load(other)
            i2 = all_insn(p2, b2, md)
            h2 = find_imm(i2, imm)
            show(i2, h2, ctx, "%s  imm 0x%x" % (other, imm))
            sa = set(x[3] + ' ' + x[4] for x in hits)
            sb = set(x[3] + ' ' + x[4] for x in h2)
            print("   MULTISET diff for imm 0x%x: only-in-first %d, only-in-second %d" %
                  (imm, len(sa - sb), len(sb - sa)))
            for x in sorted(sa - sb):
                print("      only1: %s" % x)
            for x in sorted(sb - sa):
                print("      only2: %s" % x)
            print()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
