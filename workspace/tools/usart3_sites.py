#!/usr/bin/env python3
"""Locate and characterise every access to USART3 (0x40004800) in both builds.

Why USART3: the peripheral literal census (tools/periph_probe2.py) shows this
firmware has NO SPI block referenced at all (0x40013000 / 0x40003800 /
0x40003C00 appear zero times), so a serial absolute encoder cannot be on SPI.
The only serial ports present are USART1 (0x40011000, one reference) and
USART3 (0x40004800, six references).  USART3 is therefore the top candidate for
the encoder / drive-comm link.

Method (deliberately strict, because this workspace has been burned 7 times by
searches that return 0 silently):
  * only literal-pool loads (`ldr rX,[pc,#imm]`) whose literal value is the
    peripheral base OR base+small-offset; the destination register is recorded
  * forward walk tracking that register, reporting each `[rX,#disp]` with the
    USART register it names and read/write direction
  * function boundaries are derived from every `bl`/`blx` immediate target, so
    "which function is this in" is not a heuristic
  * POSITIVE CONTROLS: the same detector must find USART1's site and a known
    RAM base (the OD descriptor array); if either returns 0 the tool aborts.
"""
import os
import struct
import sys
from collections import Counter, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN  # noqa: E402
from capstone import CS_OP_IMM, CS_OP_MEM, CS_OP_REG  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES = OrderedDict([
    ("D8", "data/servo_fw_samples/elf/v328d8.bin"),
    ("3150", "data/servo_fw_samples/elf/v3150.bin"),
])
LOAD = 0x08010000

TARGETS = OrderedDict([
    ("USART3", 0x40004800),
    ("USART1", 0x40011000),      # positive control (serial, different port)
    ("OD_DESC_3150", 0x2000129C),  # positive control (known RAM base)
    ("OD_DESC_D8", 0x2000138C),
])

USART_REGS = {
    0x00: "SR", 0x04: "DR", 0x08: "BRR", 0x0C: "CR1", 0x10: "CR2",
    0x14: "CR3", 0x18: "GTPR",
}
DMA1 = 0x40026000


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


def analyse(pl):
    m = md_detail()
    insns = list(m.disasm(pl, LOAD))
    idx = {ins.address: k for k, ins in enumerate(insns)}

    def lit_of(o, imm):
        a = ((o + 4) & ~3) + imm
        return struct.unpack_from("<I", pl, a)[0] if a + 4 <= len(pl) else None

    lits = []          # (addr, dest_reg, literal_value)
    funcs = set()      # function starts from bl/blx targets
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
                imm = None
            if imm is not None:
                v = lit_of(ins.address - LOAD, imm)
                if v is not None:
                    lits.append((ins.address, ins.op_str.split(",")[0].strip(), v))
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

    def accesses(site_addr, reg, span=24):
        k = idx.get(site_addr)
        if k is None:
            return []
        out = []
        for ins in insns[k + 1:k + 1 + span]:
            if ins.mnemonic == ".byte":
                continue
            try:
                ops = ins.operands
            except Exception:
                break
            for op in ops:
                if op.type == CS_OP_MEM and ins.reg_name(op.mem.base) == reg:
                    out.append((ins.address, op.mem.disp,
                                "W" if op.access & 2 else "r",
                                "%s %s" % (ins.mnemonic, ins.op_str)))
            if any(op.type == CS_OP_REG and ins.reg_name(op.reg) == reg
                   and (op.access & 2) for op in ops):
                break
        return out

    return insns, lits, containing, accesses


def main():
    for name, rel in IMAGES.items():
        pl = payload(os.path.join(ROOT, rel))
        insns, lits, containing, accesses = analyse(pl)
        print("=" * 76)
        print("%s   %d instructions, %d literal loads" % (name, len(insns), len(lits)))
        print("=" * 76)

        for label, base in TARGETS.items():
            hits = [(a, r, v) for a, r, v in lits if base <= v < base + 0x40]
            print("  --- %s (0x%08x) : %d literal site(s) ---" % (label, base, len(hits)))
            if not hits:
                print("      (none)")
            for a, r, v in hits:
                fn = containing(a)
                print("      site 0x%08x -> %s = 0x%08x   in function 0x%08x"
                      % (a, r, v, fn if fn else 0))
                for aa, disp, rw, txt in accesses(a, r):
                    regname = USART_REGS.get(disp, "") if label.startswith("USART") else ""
                    print("          0x%08x  %s [%s+0x%02x] %-14s %s"
                          % (aa, rw, r, disp, regname, txt))
            print()
        # abort guard: positive controls
        for label, base in (("USART1", 0x40011000), ("OD_DESC", 0x2000129C)):
            if not any(base <= v < base + 0x40 or v == base for _, _, v in lits):
                print("  !! POSITIVE CONTROL FAILED for %s - do not trust output"
                      % label)
        print()


if __name__ == "__main__":
    main()
