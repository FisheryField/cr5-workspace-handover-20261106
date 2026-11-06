#!/usr/bin/env python3
"""Read + diff a PAIR of corresponding functions from the two builds.

Usage: edit PAIRS below.  Function extents come from bl/blx targets, so the
boundaries are derived, not guessed.  The normalised diff replaces absolute
code/RAM addresses with tokens so pure relocation cancels.

Target here: the only strict-verified presence/absence difference in the
peripheral layer - D8 0x08013C08 reads TIM10_CNT and TIM11_CNT 4x each,
3150 0x08013B24 reads only TIM11_CNT 2x and never TIM10_CNT.
"""
import difflib
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN  # noqa: E402
from capstone import CS_OP_IMM, CS_OP_MEM  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOAD = 0x08010000
PAIRS = [("D8", "data/servo_fw_samples/elf/v328d8.bin", 0x08013C08,
          "3150", "data/servo_fw_samples/elf/v3150.bin", 0x08013B24),
         ("D8", "data/servo_fw_samples/elf/v328d8.bin", 0x08020514,
          "3150", "data/servo_fw_samples/elf/v3150.bin", 0x0801FE78)]


def payload(p):
    d = open(p, "rb").read()
    if d[:4] == bytes.fromhex("d4c3b2a1"):
        d = d[0x20:]
    return d


def md_detail():
    m = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    m.skipdata = True
    m.detail = True
    return m


_cache = {}


def load(rel):
    if rel in _cache:
        return _cache[rel]
    pl = payload(os.path.join(ROOT, rel))
    m = md_detail()
    insns = list(m.disasm(pl, LOAD))
    funcs = set()
    for ins in insns:
        if ins.mnemonic == ".byte":
            continue
        try:
            ops = ins.operands
        except Exception:
            continue
        if ops and ops[0].type == CS_OP_IMM and ins.mnemonic in ("bl", "blx"):
            funcs.add(ops[0].imm & ~1)
    _cache[rel] = (pl, insns, sorted(funcs))
    return _cache[rel]


def extent(rel, start):
    pl, insns, funcs = load(rel)
    nxt = [f for f in funcs if f > start]
    end = nxt[0] if nxt else start + 0x800
    return [i for i in insns if start <= i.address < min(end, start + 0x800)]


def dump(tag, rel, start):
    body = extent(rel, start)
    print("=" * 78)
    print("%s  function 0x%08x  (%d instructions)" % (tag, start, len(body)))
    print("=" * 78)
    for i in body:
        note = ""
        for op in getattr(i, "operands", []):
            if op.type == CS_OP_MEM and op.mem.disp in (0x00, 0x24, 0x2C, 0x28, 0x34):
                note += "  [disp=0x%02x]" % op.mem.disp
        print("   +0x%04x 0x%08x  %-10s %-30s%s"
              % (i.address - start, i.address, i.mnemonic, i.op_str, note))
    print()
    return body


def norm(body):
    out = []
    for i in body:
        t = "%s %s" % (i.mnemonic, i.op_str)
        t = re.sub(r"#0x8[01][0-9a-f]{5}", "#<abs>", t)
        t = re.sub(r"#0x2000[0-9a-f]{4}", "#<ram>", t)
        out.append(t)
    return out


def main():
    for tagA, relA, aA, tagB, relB, aB in PAIRS:
        ba = dump(tagA, relA, aA)
        bb = dump(tagB, relB, aB)
        na, nb = norm(ba), norm(bb)
        sm = difflib.SequenceMatcher(None, na, nb, autojunk=False)
        same = sum(b.size for b in sm.get_matching_blocks())
        print("=" * 78)
        print("DIFF %s(0x%08x, %d insns)  vs  %s(0x%08x, %d insns)"
              % (tagA, aA, len(na), tagB, aB, len(nb)))
        print("matched %d/%d = %.1f%%"
              % (same, max(len(na), len(nb)), 100.0 * same / max(len(na), len(nb))))
        print("=" * 78)
        n = 0
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == "equal":
                continue
            n += 1
            if n > 25:
                print("  ... more")
                break
            print("  %-8s %s[%d:%d] vs %s[%d:%d]" % (op, tagA, i1, i2, tagB, j1, j2))
            for x in na[i1:i2][:6]:
                print("      %-5s %s" % (tagA, x))
            for y in nb[j1:j2][:6]:
                print("      %-5s %s" % (tagB, y))
        print()


if __name__ == "__main__":
    main()
