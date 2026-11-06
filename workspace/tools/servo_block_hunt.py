#!/usr/bin/env python3
"""Locate a code block's counterpart in another build by *instruction shape*,
not by address arithmetic.

Reason: the two images differ in size (~9 KB) and blocks are relocated
non-uniformly, so `addr_in_B = addr_in_A + delta` is invalid.

Method: disassemble a window of build A, turn it into a skeleton where every
operand that is an *absolute address* is replaced by a placeholder, then slide
that skeleton over build B and report matches.

Usage:
  servo_block_hunt.py <A.bin> <B.bin> --at 0x080216D4 --len 0x40
  servo_block_hunt.py ... --at ... --len ... --mask-imm
"""
import argparse
import re
import sys

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN

from servo_img import FLASH_BASE as BASE, load_image

IMM8_RE = re.compile(r"#0x[0-9a-f]+$")
ADDR_RE = re.compile(r"#0x08[0-9a-f]{6}")


def load(path):
    """Header-stripped flash image (the .bin files carry a ~0x20 byte vendor
    header; slicing raw file offsets disassembles shifted garbage silently)."""
    return load_image(path)[2]


def dis(data, off, size):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.detail = False
    b = data[off:off + size]
    return list(md.disasm(b, BASE + off))


def skeleton(insns, mask_imm):
    """Return a list of (mnemonic, operand-skeleton) pairs.

    Absolute branch targets are rewritten as *relative displacements* so the same
    control flow matches even when the block sits at a different address.
    (Without this every `cbnz #0x8010ea4` fails to match its relocated copy, and
    the matcher silently reports "none".)
    """
    out = []
    for i in insns:
        ops = i.op_str

        # 1) branch targets: capstone may print them as #0x0801xxxx (hex) or as a
        #    decimal.  Rewrite to a relative displacement so relocation matches.
        def branch_rel(m):
            tok = m.group(1)
            try:
                tgt = int(tok, 16) if tok.lower().startswith("0x") else int(tok, 10)
            except ValueError:
                return m.group(0)
            if 0x08000000 <= tgt < 0x08200000:
                return "#REL%+d" % (tgt - i.address)
            return m.group(0)

        ops = re.sub(r"#(0x[0-9a-fA-F]+|\d+)", branch_rel, ops)
        # 2) remaining absolute flash addresses (literal pointer operands)
        ops = re.sub(r"#(0x08[0-9a-f]{6})", "#ADDR", ops)

        if mask_imm:
            # 3) small constants: PC-relative literal offsets and struct offsets move
            #    between builds, so collapse anything short.
            ops = re.sub(r"#(0x[0-9a-f]{1,3}|-?0x[0-9a-f]{1,3})\b", "#SMALL", ops)

        out.append((i.mnemonic, ops))
    return out


def score(a, b):
    """Fraction of aligned instruction-shape matches, 0..1.

    Length-tolerant: the two builds may differ in instruction count inside the
    same logical block, so require the sequences to be *comparable in length*
    and score over max(len) so an inserted/removed instruction lowers the score
    instead of being silently skipped (the old strict `len(ins_b) != len(ins_a)`
    filter rejected every relocated block).
    """
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    m = max(len(a), len(b))
    if n < 8 or n / m < 0.7:
        return 0.0
    same = sum(1 for x, y in zip(a[:n], b[:n]) if x == y)
    return same / m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--at", required=True, help="start address in build A (hex)")
    ap.add_argument("--len", default="0x40", help="block length in bytes")
    ap.add_argument("--mask-imm", action="store_true",
                    help="also mask small immediates (needed when field offsets shift)")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--stride", type=int, default=2)
    ap.add_argument("--min-score", type=float, default=0.60)
    args = ap.parse_args()

    at = int(args.at, 16)
    size = int(args.len, 16)
    da, db = load(args.a), load(args.b)

    off_a = at - BASE
    ins_a = dis(da, off_a, size)
    if not ins_a:
        print("no instructions decoded in A window", file=sys.stderr)
        return 1
    skel_a = skeleton(ins_a, args.mask_imm)

    print("=== build A block ===")
    for i in ins_a:
        print("  %08x: %-10s %s" % (i.address, i.mnemonic, i.op_str))

    if args.mask_imm:
        print("\n=== A skeleton (small imms masked) ===")
        print("  " + " | ".join("%s %s" % m for m in skel_a))

    # slide over build B on 2-byte grid
    hits = []
    for off in range(0, len(db) - size, args.stride):
        ins_b = dis(db, off, size)
        if not ins_b:
            continue
        s = score(skel_a, skeleton(ins_b, args.mask_imm))
        if s >= args.min_score:
            hits.append((s, off + BASE))

    hits.sort(reverse=True)
    print("\n=== candidates in build B (top %d, min score %.2f) ===" % (args.top, args.min_score))
    if not hits:
        print("  none")
    seen = []
    for s, addr in hits:
        if any(abs(addr - p) < size for p in seen):
            continue
        seen.append(addr)
        print("  %08x  score %.3f  (A %08x + %+d)" % (addr, s, at, addr - at))
        ins_b = dis(db, addr - BASE, size)
        for i in ins_b:
            print("        %08x: %-10s %s" % (i.address, i.mnemonic, i.op_str))
        if len(seen) >= args.top:
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
