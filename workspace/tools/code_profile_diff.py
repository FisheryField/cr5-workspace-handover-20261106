#!/usr/bin/env python3
"""WHERE is D8's extra code?

D8 payload = 338,072 B, 3150 = 328,860 B -> D8 is 9,212 bytes bigger.  The
feature-level diff (tools/feature_diff3.py) found no new strings, no new ISR and
no new peripheral block except USB-OTG-FS, so the added bytes are the best
remaining localiser for "what did the D8 build add".

Method: histogram function starts (bl/blx targets) and decoded instructions in
0x1000-byte address windows for both builds, then report the windows where the
two profiles differ most.  A window where D8 has many functions and 3150 none is
a D8-only module.

Positive controls: the vector-table window 0x08010000 must be populated in both,
and the total function counts must be in the thousands (the images decode
151,248 / 148,648 instructions - see AGENTS.md).  If a control fails the tool
aborts rather than printing a misleading table.
"""
import os
import struct
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN  # noqa: E402
from capstone import CS_OP_IMM  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES = [("D8", "data/servo_fw_samples/elf/v328d8.bin"),
          ("3150", "data/servo_fw_samples/elf/v3150.bin")]
LOAD = 0x08010000
WIN = 0x1000


def payload(p):
    d = open(p, "rb").read()
    if d[:4] == bytes.fromhex("d4c3b2a1"):
        d = d[0x20:]
    return d


def profile(pl):
    m = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    m.skipdata = True
    m.detail = True
    funcs = Counter()
    insns = Counter()
    n_ins = 0
    for ins in m.disasm(pl, LOAD):
        w = (ins.address - LOAD) // WIN
        if ins.mnemonic == ".byte":
            continue
        n_ins += 1
        insns[w] += 1
        try:
            ops = ins.operands
        except Exception:
            continue
        if ops and ops[0].type == CS_OP_IMM and ins.mnemonic in ("bl", "blx"):
            funcs[(ops[0].imm - LOAD) // WIN] += 1
    return funcs, insns, n_ins


def main():
    prof = {}
    for tag, rel in IMAGES:
        pl = payload(os.path.join(ROOT, rel))
        prof[tag] = profile(pl)
        f, i, n = prof[tag]
        print("%-5s payload %7d B   instructions %6d   functions %5d"
              % (tag, len(pl), n, sum(f.values())))

    # positive controls
    ok = True
    for tag in ("D8", "3150"):
        f, i, n = prof[tag]
        if n < 100000:
            print("  !! control failed: only %d instructions in %s" % (n, tag))
            ok = False
        if i.get(0, 0) < 20:
            print("  !! control failed: window 0 has %d insns in %s"
                  % (i.get(0, 0), tag))
            ok = False
    print("controls: %s" % ("PASS" if ok else "FAIL"))
    if not ok:
        return 2

    print()
    print("=" * 78)
    print("WINDOW PROFILE DIFF (0x1000-byte windows)")
    print("=" * 78)
    print("  window      addr        D8:fn/ins    3150:fn/ins    d(ins)")
    keys = sorted(set(prof["D8"][0]) | set(prof["3150"][0]) |
                  set(prof["D8"][1]) | set(prof["3150"][1]))
    rows = []
    for w in keys:
        a_f = prof["D8"][0].get(w, 0)
        b_f = prof["3150"][0].get(w, 0)
        a_i = prof["D8"][1].get(w, 0)
        b_i = prof["3150"][1].get(w, 0)
        rows.append((w, a_f, b_f, a_i, b_i, a_i - b_i))
    # show every window where one side has functions and the other has none,
    # or where the instruction delta is large
    print("  -- windows where ONE build has functions and the other has none --")
    for w, a_f, b_f, a_i, b_i, d in rows:
        if (a_f > 0) != (b_f > 0):
            print("     win %-5d 0x%08x   D8 %3dfn/%4dins   3150 %3dfn/%4dins  %s"
                  % (w, LOAD + w * WIN, a_f, a_i, b_f, b_i,
                     "D8-ONLY" if a_f else "3150-ONLY"))
    print()
    print("  -- top 20 windows by |instruction delta| --")
    for w, a_f, b_f, a_i, b_i, d in sorted(rows, key=lambda r: -abs(r[5]))[:20]:
        print("     win %-5d 0x%08x   D8 %3dfn/%4dins   3150 %3dfn/%4dins  %+d"
              % (w, LOAD + w * WIN, a_f, a_i, b_f, b_i, d))
    print()
    tot_a = sum(r[3] for r in rows)
    tot_b = sum(r[4] for r in rows)
    print("  total instructions D8 %d / 3150 %d  (delta %+d)"
          % (tot_a, tot_b, tot_a - tot_b))
    print("  SUM of positive deltas : %+d   SUM of negative deltas : %+d"
          % (sum(r[5] for r in rows if r[5] > 0),
             sum(r[5] for r in rows if r[5] < 0)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
