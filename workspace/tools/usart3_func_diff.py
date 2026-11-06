#!/usr/bin/env python3
"""Dump and diff the USART3-owning function in both builds.

Established by tools/usart3_sites.py:
  D8   0x0802CF50   USART3 refs at function+0x196/0x1C6/0x1EA/0x220/0x256/0x25E
  3150 0x0802BA7C   USART3 refs at function+0x196/0x1C6/0x1EA/0x220/0x256/0x25E
The relative offsets are identical, so this is the same routine in both builds.
Here the whole function is emitted for both, plus a normalised diff that
replaces absolute branch/branch-link targets with symbolic tokens, so a real
logic difference can be told apart from pure relocation.
"""
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN  # noqa: E402
from capstone import CS_OP_IMM  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOAD = 0x08010000
FUNCS = {"D8": (0x0802CF50, "data/servo_fw_samples/elf/v328d8.bin"),
         "3150": (0x0802BA7C, "data/servo_fw_samples/elf/v3150.bin")}
MAXLEN = 0x400          # stop after this many bytes at the latest


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


def collect(pl):
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
    return insns, sorted(funcs)


def main():
    out = {}
    for name, (start, rel) in FUNCS.items():
        pl = payload(os.path.join(ROOT, rel))
        insns, funcs = collect(pl)
        nxt = [f for f in funcs if f > start]
        end = nxt[0] if nxt else start + MAXLEN
        end = min(end, start + MAXLEN)
        body = [i for i in insns if start <= i.address < end]
        out[name] = (body, start, end)
        print("=" * 76)
        print("%s   function 0x%08x .. 0x%08x  (%d instructions, %d bytes)"
              % (name, start, end, len(body), end - start))
        print("=" * 76)
        for i in body:
            rel_off = i.address - start
            mark = " <<< USART3" if i.address in (
                {0x0802d0e6, 0x0802d116, 0x0802d13a, 0x0802d170, 0x0802d1a6, 0x0802d1ae}
                if name == "D8" else
                {0x0802bc12, 0x0802bc42, 0x0802bc66, 0x0802bc9c, 0x0802bcd2, 0x0802bcda}
            ) else ""
            print("   +0x%04x  0x%08x  %-10s %s%s"
                  % (rel_off, i.address, i.mnemonic, i.op_str, mark))
        print()

    # normalised diff
    print("=" * 76)
    print("NORMALISED DIFF (absolute targets -> <abs>, so pure relocation cancels)")
    print("=" * 76)
    def norm(body):
        s = []
        for i in body:
            txt = "%s %s" % (i.mnemonic, i.op_str)
            txt = re.sub(r"#0x8[01][0-9a-f]{5}", "#<abs>", txt)
            txt = re.sub(r"#0x2000[0-9a-f]{4}", "#<ram>", txt)
            s.append(txt)
        return s
    a = norm(out["D8"][0])
    b = norm(out["3150"][0])
    import difflib
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    same = sum(bl.size for bl in sm.get_matching_blocks())
    print("  D8 %d insns, 3150 %d insns, matched %d  (%.1f%%)"
          % (len(a), len(b), same, 100.0 * same / max(len(a), len(b))))
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        print("  %-8s D8[%d:%d] vs 3150[%d:%d]" % (tag, i1, i2, j1, j2))
        for x in a[i1:i2][:8]:
            print("       D8   %s" % x)
        for y in b[j1:j2][:8]:
            print("       3150 %s" % y)


if __name__ == "__main__":
    main()
