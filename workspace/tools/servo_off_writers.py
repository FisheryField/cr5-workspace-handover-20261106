#!/usr/bin/env python3
"""Find every site that loads/stores a given constant offset relative to ANY
indexed base register, i.e. the idiom

    mov.w/movs rX, #<off>
    ldr/str  rY, [rX, rZ]        (or the reverse order, or [rX,#imm])

This is the addressing shape this firmware uses for per-axis arrays where the
offset does not fit a 12-bit single-instruction displacement.

Motivation (this session): the struct offsets for the *same* logical field
disagree between the two builds in different places (+8 in one block, -0x18 in
another).  Guessing which block owns `mode` produced a wrong documented table,
so enumerate the writers of every candidate offset and read them.

Usage:
  servo_off_writers.py <bin> --offs 0xb4,0xcc --tol 8
"""
import argparse
import traceback
import sys
from collections import defaultdict

from servo_img import FLASH_BASE as BASE, load_image, make_md


def scan(path, offs, tol):
    _raw, _hdr, code = load_image(path)
    md = make_md()          # skipdata: whole-image sweep (see servo_img)
    insns = list(md.disasm(code, BASE))

    want = {}
    for o in offs:
        for d in range(-tol, tol + 1):
            want[o + d] = o

    # pending constant load: reg -> (value, address)
    pend = {}
    hits = defaultdict(list)

    for i in insns:
        m, ops = i.mnemonic, i.op_str
        const_dst = reg_of_const_form(m, ops)
        if const_dst is not None:
            v = parse_imm(ops.split(",")[1].strip())
            if v is not None:
                pend[const_dst] = (v, i.address)
                continue
        # any instruction that uses a pending register as a base/index
        if "[" in ops:
            inside = ops.split("[", 1)[1]
            for reg, (v, src) in list(pend.items()):
                if reg in inside and v in want:
                    hits[want[v]].append((i.address, m, ops, v, src))
        # invalidate when the register is overwritten by a non-constant load
        if m.startswith("ldr") or m.startswith("add") or m.startswith("sub"):
            pend.pop(ops.split(",")[0].strip(), None)
    return hits


def reg_of_const_form(m, ops):
    """The register written by a bare constant-load form, else None."""
    if m in ("mov.w", "movs", "mov") and "[pc" not in ops:
        parts = [p.strip() for p in ops.split(",")]
        if len(parts) == 2 and parts[1].startswith("#"):
            return parts[0]
    return None


def parse_imm(s):
    """'#0x1f' -> 31, '#-8' -> -8, '#08' -> 8, '#1e' -> 30.

    NOTE: int(s, 0) is wrong here - Python 3 rejects zero-padded decimals like
    '#08', and bare '#0x1e'-style values must stay hex.  This firmware mixes
    '#0x..' and plain decimal immediates in the same basic block.
    """
    if not s.startswith("#"):
        return None
    t = s[1:].strip()
    neg = t.startswith("-")
    if neg:
        t = t[1:]
    try:
        v = int(t, 16) if t.lower().startswith("0x") else int(t, 10)
    except ValueError:
        return None
    return -v if neg else v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bin")
    ap.add_argument("--offs", required=True, help="comma-separated hex offsets")
    ap.add_argument("--tol", type=int, default=8)
    args = ap.parse_args()

    offs = [int(x, 16) for x in args.offs.split(",")]
    try:
        res = scan(args.bin, offs, args.tol)
    except Exception:
        traceback.print_exc()
        return 2

    # positive control: the tool must be able to see a site we can read by eye.
    # D8 0x080216DC "movs r0,#0xcc" + 0x080216DE "str r1,[r0,r4]"; 3150 has the
    # same shape at 0x08020248 / 0x0802024A with 0xd4.
    ctrl = [(0xCC, 0x080216DE), (0xD4, 0x0802024A)]
    print("--- positive control ---")
    for off, addr in ctrl:
        found = any(a == addr for a, *_ in res.get(off, []))
        print("   subtest 0x%x should contain %08x : %s"
              % (off, addr, "PASS" if found else "not present in this image"))
    print()

    for o in offs:
        rows = res.get(o, [])
        print("=== offset 0x%x : %d accessing instruction(s) within +/-%d ===" % (o, len(rows), args.tol))
        seen = set()
        for addr, m, ops, v, src in sorted(rows):
            if addr in seen:
                continue
            seen.add(addr)
            tag = "" if v == o else "   <-- actually 0x%x" % v
            print("   %08x  %-10s %-28s (const from %08x)%s" % (addr, m, ops, src, tag))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
