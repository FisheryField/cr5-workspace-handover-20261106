#!/usr/bin/env python3
"""Strictly verify the ONE presence/absence difference found in the peripheral
layer, and read what it does.

tools/periph_probe.py (v1) counted ALIGNED DWORD literals and reported
    0x40014424 (TIM10->CNT) : D8 x5,  3150 x0
    0x40014824 (TIM11->CNT) : D8 x5,  3150 x3
    0x50000000 (USB-OTG-FS) : D8 x3,  3150 x0
That census is a [count] grade measurement and this workspace has a standing
rule that counts may only shortlist, never conclude.  So here the same claim is
re-measured with the STRICT method - actual `ldr rX,[pc,#imm]` literal loads -
and each site is attributed to its containing function (function starts derived
from bl/blx targets, not guessed).

Positive controls: TIM4 (0x40000800) and TIM5 (0x40000C00) must be found in
both builds, or the detector is broken and the tool aborts.
"""
import os
import struct
import sys
from collections import Counter, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN  # noqa: E402
from capstone import CS_OP_IMM, CS_OP_MEM  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES = OrderedDict([
    ("D8", "data/servo_fw_samples/elf/v328d8.bin"),
    ("3150", "data/servo_fw_samples/elf/v3150.bin"),
])
LOAD = 0x08010000

TARGETS = OrderedDict([
    ("TIM4     0x40000800", 0x40000800),
    ("TIM5     0x40000C00", 0x40000C00),
    ("TIM6     0x40001000", 0x40001000),
    ("TIM7     0x40001400", 0x40001400),
    ("TIM10    0x40014400", 0x40014400),
    ("TIM10_CNT 0x40014424", 0x40014424),
    ("TIM11    0x40014800", 0x40014800),
    ("TIM11_CNT 0x40014824", 0x40014824),
    ("USBFS    0x50000000", 0x50000000),
])
CONTROLS = ("TIM4     0x40000800", "TIM5     0x40000C00")


def payload(p):
    d = open(p, "rb").read()
    if d[:4] == bytes.fromhex("d4c3b2a1"):
        d = d[0x20:]
    return d


def analyse(pl):
    m = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    m.skipdata = True
    m.detail = True
    insns = list(m.disasm(pl, LOAD))
    idx = {i.address: k for k, i in enumerate(insns)}
    funcs = set()
    lits = []
    for ins in insns:
        if ins.mnemonic == ".byte":
            continue
        try:
            ops = ins.operands
        except Exception:
            continue
        if ins.mnemonic.startswith("ldr") and "[pc" in ins.op_str:
            try:
                imm = int(ins.op_str.split("#")[1].split("]")[0].strip(), 0)
            except Exception:
                continue
            a = ((ins.address - LOAD + 4) & ~3) + imm
            if a + 4 <= len(pl):
                lits.append((ins.address, ins.op_str.split(",")[0].strip(),
                             struct.unpack_from("<I", pl, a)[0]))
        if ops and ops[0].type == CS_OP_IMM and ins.mnemonic in ("bl", "blx"):
            funcs.add(ops[0].imm & ~1)
    funcs = sorted(funcs)

    def containing(addr):
        lo, hi = 0, len(funcs)
        while lo < hi:
            mid = (lo + hi) // 2
            if funcs[mid] <= addr:
                lo = mid + 1
            else:
                hi = mid
        return funcs[lo - 1] if lo else None

    def fwd(site, reg, span=16):
        out = []
        k = idx.get(site)
        if k is None:
            return out
        for ins in insns[k + 1:k + 1 + span]:
            if ins.mnemonic == ".byte":
                continue
            try:
                ops = ins.operands
            except Exception:
                break
            for op in ops:
                if op.type == CS_OP_MEM and ins.reg_name(op.mem.base) == reg:
                    out.append("0x%08x %s [%s+0x%02x]"
                               % (ins.address, "W" if op.access & 2 else "r",
                                  reg, op.mem.disp))
            if any(getattr(op, "type", None) == 1
                   and op.access & 2
                   and ins.reg_name(getattr(op, "reg", 0)) == "?"
                   for op in ops):
                break
        return out

    return lits, containing, fwd


def main():
    tables = {}
    for name, rel in IMAGES.items():
        pl = payload(os.path.join(ROOT, rel))
        lits, containing, fwd = analyse(pl)
        tables[name] = (lits, containing, fwd)
        print("=" * 78)
        print("%s  (%d literal loads)" % (name, len(lits)))
        print("=" * 78)
        for label, base in TARGETS.items():
            hits = [(a, r, v) for a, r, v in lits if v == base]
            fns = Counter(containing(a) for a, _, _ in hits)
            print("  %-22s : %2d strict site(s)   functions: %s"
                  % (label, len(hits),
                     ", ".join("0x%08x x%d" % (f, c) for f, c in fns.items())
                     or "-"))
            for a, r, v in hits[:6]:
                print("        site 0x%08x -> %s  in 0x%08x   accesses: %s"
                      % (a, r, containing(a), fwd(a, r)))
        print()

    ok = True
    for label in CONTROLS:
        base = TARGETS[label]
        for name in IMAGES:
            lits = tables[name][0]
            if not any(v == base for _, _, v in lits):
                print("  !! POSITIVE CONTROL FAILED: %s not found in %s" % (label, name))
                ok = False
    print("POSITIVE CONTROLS: %s" % ("PASS" if ok else "FAIL - do not trust the table"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
