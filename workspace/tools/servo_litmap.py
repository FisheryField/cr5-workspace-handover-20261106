#!/usr/bin/env python3
"""Resolve PC-relative literal-pool loads WITHOUT relying on capstone's
annotations.

Why this is needed: enabling `skipdata` (mandatory for whole-image sweeps, see
servo_img.make_md) SUPPRESSES capstone's `; lit@0x... = 0x...` annotations.
Any tool that parses those annotations therefore silently returns 0 results on a
full sweep.  This firmware loads all 32-bit constants from literal pools, so
resolving them by hand is essential.

Thumb PC-relative load:  base = (insn_addr + 4) & ~3   (word-aligned)
                         value = dword at (base + imm)
"""
import sys

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image, make_md


def resolve_literals(path, verbose=False):
    """Return {insn_addr: (mnemonic, op_str, pool_addr, value)} for every
    PC-relative load."""
    _r, _h, code = load_image(path)
    md = make_md()
    out = {}
    for i in md.disasm(code, FLASH_BASE):
        if not i.op_str.startswith(("r", "s")) or "[pc" not in i.op_str:
            continue
        try:
            imm = int(i.op_str.split("#")[-1].rstrip("]"), 16)
        except ValueError:
            continue
        pool = ((i.address + 4) & ~3) + imm
        off = pool - FLASH_BASE
        if off < 0 or off + 4 > len(code):
            continue
        val = int.from_bytes(code[off:off + 4], "little")
        out[i.address] = (i.mnemonic, i.op_str, pool, val)
        if verbose:
            print("  %08x %-8s %-24s -> 0x%08x = 0x%08x"
                  % (i.address, i.mnemonic, i.op_str, pool, val))
    return out


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/servo_fw_samples/elf/v328d8.bin"
    lit = resolve_literals(path, verbose=False)
    print("resolved %d PC-relative literal loads in %s" % (len(lit), path))
    for addr in (0x0802143A, 0x08021444, 0x08021452):
        print("  %08x -> %s" % (addr, lit.get(addr)))


if __name__ == "__main__":
    main()
