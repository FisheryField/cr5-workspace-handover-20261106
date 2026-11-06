#!/usr/bin/env python3
"""Field-level role of the four globals around the patch site, both builds.

MOTIVATION
  tools/servo_ramglobals_census.py showed the two builds have PARALLEL
  two-struct layouts:
      D8   : 0x20003ED4 (+20 sites)  and  0x20003ED4+0x24 = 0x20003EF8 (+17)
      3150 : 0x20003D8C (+22 sites)  and  0x20003D8C+0x24 = 0x20003DB0 (+79)
  So "D8 has 0 references to 0x20003DB0" was comparing the wrong pair - D8's
  counterpart is 0x20003EF8 and it IS referenced.  The open question is whether
  D8's counterpart also holds a "+0x18 correction" that D8 folds into the
  position result somewhere else.

METHOD (per site, not per address, so the base register is known)
  Find every literal load that names the base, record the destination register,
  then walk forward up to 12 instructions reporting each access `[rK,#imm]`
  with its read/write direction.  Stop early if rK is overwritten.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from servo_img import make_md  # noqa: E402
from capstone import (Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN,
                      CS_OP_MEM, CS_OP_REG, CS_OP_IMM)  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES = {
    "D8": (os.path.join(ROOT, "data/servo_fw_samples/elf/v328d8.bin"),
           [0x20003ed4, 0x20003ef8]),
    "3150": (os.path.join(ROOT, "data/servo_fw_samples/elf/v3150.bin"),
             [0x20003d8c, 0x20003db0]),
}
LOAD = 0x08010000
RAM_LO, RAM_HI = 0x20000000, 0x20100000


def payload(p):
    d = open(p, "rb").read()
    if d[:4] == bytes.fromhex("d4c3b2a1"):
        d = d[0x20:]
    return d


def lit(pl, i, imm):
    a = ((i + 4) & ~3) + imm
    if a + 4 > len(pl):
        return None
    return struct.unpack_from("<I", pl, a)[0]


def all_insns(pl):
    # detail=True is REQUIRED for ins.operands; servo_img.make_md() leaves it
    # off on purpose (faster sweeps), so build a local decoder here.
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.skipdata = True
    md.detail = True
    return list(md.disasm(pl, LOAD))


def literal_sites(pl, insns, target):
    """[(insn_index, dest_reg_name)] for loads of `target`."""
    out = []
    for k, ins in enumerate(insns):
        if not (ins.mnemonic.startswith("ldr") and "[pc" in ins.op_str):
            continue
        try:
            imm = int(ins.op_str.split("#")[1].split("]")[0].strip(), 0)
        except Exception:
            continue
        if lit(pl, ins.address - LOAD, imm) != target:
            continue
        dst = ins.op_str.split(",")[0].strip()
        out.append((k, dst))
    return out


def accesses(insns, k, reg, span=14):
    """Report memory accesses through `reg` after instruction k."""
    rows = []
    for ins in insns[k + 1:k + 1 + span]:
        if ins.mnemonic == ".byte":
            continue
        wrote = False
        try:
            ops = ins.operands
        except Exception:
            break
        for op in ops:
            if op.type == CS_OP_REG and ins.reg_name(op.reg) == reg and op.access & 2:
                wrote = True
        txt = "%s %s" % (ins.mnemonic, ins.op_str)
        for op in ops:
            if op.type == CS_OP_MEM and ins.reg_name(op.mem.base) == reg:
                d = "W" if op.access & 2 else "r"
                rows.append((d, op.mem.disp, ins.address, txt))
        if wrote:
            break
    return rows


def main():
    out = []
    P = out.append
    for name, (path, targets) in IMAGES.items():
        pl = payload(path)
        insns = all_insns(pl)
        P("=" * 78)
        P("%s   (%d instructions)" % (name, len(insns)))
        P("=" * 78)
        for t in targets:
            sites = literal_sites(pl, insns, t)
            P("")
            P("  --- base 0x%08x : %d load site(s) ---" % (t, len(sites)))
            tally = {}
            for k, reg in sites:
                rows = accesses(insns, k, reg)
                desc = "  ".join("%s%+#x" % (d, off) for d, off, _, _ in rows)
                P("    0x%08x  %-4s -> %s"
                  % (insns[k].address, reg, desc if desc else "(no access seen)"))
                for d, off, a, _ in rows:
                    tally.setdefault((d, off), []).append(a)
            P("    field tally:")
            for (d, off) in sorted(tally, key=lambda x: (x[1], x[0])):
                P("       %s %+#06x  : %2d site(s)  %s"
                  % (d, off, len(tally[(d, off)]),
                     " ".join("0x%08x" % a for a in tally[(d, off)][:8])))
        P("")

    txt = "\n".join(out)
    dst = os.path.join(ROOT, "data/servo_fw_samples/GLOBAL_ROLES.txt")
    with open(dst, "w", encoding="utf-8") as f:
        f.write(txt + "\n")
    # console: only the tallies, which is the decision-relevant part
    keep = [l for l in out if ("tally" in l or l.startswith("  ---")
                               or l.startswith("D8") or l.startswith("3150")
                               or l.startswith("       ") or l.startswith("="))]
    print("\n".join(keep).encode("ascii", "replace").decode("ascii"))
    print("\n[written] %s" % dst)


if __name__ == "__main__":
    main()
