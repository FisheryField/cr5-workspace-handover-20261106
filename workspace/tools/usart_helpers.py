#!/usr/bin/env python3
"""Read the USART helper routines called with a USART base in r0.

The per-axis init function in both builds calls
    0x0801B84C   with r0 = 0x40004800, r1 = 1
    0x0801B778   with r0 = 0x40004800, r1 = &config
and those two contain the actual register-level work (which is why the caller
shows no [base+disp] access).  This dumps them plus their neighbourhood in both
builds, marking every memory access whose displacement looks like a USART
register (SR=0, DR=4, BRR=8, CR1=0xC, CR2=0x10, CR3=0x14, GTPR=0x18).
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN  # noqa: E402
from capstone import CS_OP_IMM, CS_OP_MEM  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOAD = 0x08010000
WINDOWS = {
    "D8": ("data/servo_fw_samples/elf/v328d8.bin", 0x0801B700, 0x0801B900),
    "3150": ("data/servo_fw_samples/elf/v3150.bin", 0x0801B0A0, 0x0801B2C0),
}
USART_REGS = {0x00: "SR", 0x04: "DR", 0x08: "BRR", 0x0C: "CR1",
              0x10: "CR2", 0x14: "CR3", 0x18: "GTPR"}


def payload(p):
    d = open(p, "rb").read()
    if d[:4] == bytes.fromhex("d4c3b2a1"):
        d = d[0x20:]
    return d


def main():
    for name, (rel, lo, hi) in WINDOWS.items():
        pl = payload(os.path.join(ROOT, rel))
        m = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
        m.skipdata = True
        m.detail = True
        allins = list(m.disasm(pl, LOAD))
        funcs = set()
        for ins in allins:
            if ins.mnemonic == ".byte":
                continue
            try:
                ops = ins.operands
            except Exception:
                continue
            if ops and ops[0].type == CS_OP_IMM and ins.mnemonic in ("bl", "blx"):
                funcs.add(ops[0].imm & ~1)

        def lit(o, imm):
            a = ((o + 4) & ~3) + imm
            return struct.unpack_from("<I", pl, a)[0] if a + 4 <= len(pl) else None

        print("=" * 78)
        print("%s   window 0x%08x .. 0x%08x" % (name, lo, hi))
        print("=" * 78)
        for ins in allins:
            if not (lo <= ins.address < hi):
                continue
            note = ""
            if ins.mnemonic.startswith("ldr") and "[pc" in ins.op_str:
                try:
                    imm = int(ins.op_str.split("#")[1].split("]")[0].strip(), 0)
                    note = "   ; = 0x%08x" % (lit(ins.address - LOAD, imm),)
                except Exception:
                    pass
            for op in getattr(ins, "operands", []):
                if op.type == CS_OP_MEM and op.mem.disp in USART_REGS \
                        and ins.reg_name(op.mem.base).startswith("r"):
                    note += "   <USART %s>" % USART_REGS[op.mem.disp]
            fs = "FUNC->" if ins.address in funcs else "       "
            print("  %s 0x%08x  %-10s %-30s%s"
                  % (fs, ins.address, ins.mnemonic, ins.op_str, note))
        print()


if __name__ == "__main__":
    main()
