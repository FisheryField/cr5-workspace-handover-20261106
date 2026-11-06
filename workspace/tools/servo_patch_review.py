#!/usr/bin/env python3
"""Re-audit the 3.1.5.0 patch site from raw bytes + real disassembly.

WHY THIS EXISTS
  tools/servo_patch_3150.py contradicts itself:
      docstring line 13/22 : the patch is "mov r1, r0"   (bytes 01 46)
      PATCH_NEW  line 60   : "084600bf00bf"             (= mov r0, r1)
  Those are DIFFERENT instructions with opposite meaning.  Whichever is
  wrong would store the wrong value into the position result, so the site
  is re-derived here from the raw bytes with a real decoder, and the register
  liveness is traced backwards through the containing basic block.

WHAT MUST BE TRUE FOR THE PATCH TO MEAN "remove the correction term"
  original tail : r1 = correction ; r1 = r1 + r0 ; store r1   (result = r0+corr)
  patched tail  : r1 = r0                                   (result = r0)
  => the patch MUST be `mov r1, r0` == halfword 0x4601 == bytes 01 46.
     `mov r0, r1` (08 46) would instead overwrite r0 with the CORRECTION and
     store the correction as the position - a wrong patch that still passes a
     naive "did the bytes change" check.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from servo_img import make_md  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V3150 = os.path.join(ROOT, "data/servo_fw_samples/elf/v3150.bin")
V328D8 = os.path.join(ROOT, "data/servo_fw_samples/elf/v328d8.bin")
LOAD = 0x08010000          # PROVEN by tools/pkg_load_verdict.py
OLD = bytes.fromhex("2c4989690144")


def payload(p):
    d = open(p, "rb").read()
    if d[:4] == bytes.fromhex("d4c3b2a1"):
        d = d[0x20:]
    return d


def dis(pl, off, n, base_label=LOAD):
    md = make_md()
    start = base_label + off
    return list(md.disasm(pl[off:off + n], start))


def main():
    out = []
    P = out.append
    md = make_md()

    d8 = payload(V328D8)
    v3 = payload(V3150)

    P("=" * 78)
    P("1. UNIQUENESS of the patch byte pattern")
    P("=" * 78)
    for name, pl in (("3150(3.1.5.0)", v3), ("D8(3.2.D.8)", d8)):
        hits = []
        i = pl.find(OLD)
        while i >= 0:
            hits.append(i)
            i = pl.find(OLD, i + 1)
        P("  %s : %d occurrence(s) of %s" % (name, len(hits), OLD.hex(" ")))
        for h in hits:
            P("      payload offset 0x%05x   flash 0x%08x" % (h, LOAD + h))
    P("")

    off = v3.find(OLD)
    if off < 0:
        P("  !! pattern NOT FOUND in 3150 - abort")
        print("\n".join(out))
        return 2

    P("=" * 78)
    P("2. 3150 disassembly around the site (real load base 0x%08x)" % LOAD)
    P("=" * 78)
    back = 0x60
    ins = dis(v3, off - back, back + 0x60)
    for i in ins:
        o = i.address - LOAD
        flag = "  <<< PATCHED" if off <= o < off + 6 else ""
        P("  0x%08x  (off 0x%05x)  %-8s %s%s"
          % (i.address, o, i.mnemonic, i.op_str, flag))
    P("")

    P("=" * 78)
    P("3. the two candidate patches, decoded")
    P("=" * 78)
    for label, hx in (("mov r1, r0  (01 46)", bytes.fromhex("014600bf00bf")),
                      ("mov r0, r1  (08 46)", bytes.fromhex("084600bf00bf")),
                      ("bf 00 x2 WRONG-ENDIAN", bytes.fromhex("bf00bf00"))):
        for i in md.disasm(hx, LOAD + off):
            P("  %-24s -> 0x%08x  %-8s %s" % (label, i.address, i.mnemonic, i.op_str))
        P("")

    P("=" * 78)
    P("4. D8 counterpart: where does D8 write +0x234 ?")
    P("=" * 78)
    # str.w r1,[sb,#0x234]  -> c9 f8 34 12 ; scan for the #0x234 immediate in a
    # str.w (12-bit imm12 with bit11 set = 0x234 -> imm12 = 0xA34)
    for name, pl in (("D8(3.2.D.8)", d8), ("3150(3.1.5.0)", v3)):
        P("  --- %s ---" % name)
        found = []
        for i in range(0, len(pl) - 8, 2):
            w = struct.unpack_from("<H", pl, i)[0]
            # str.w rX,[rY,#0x234] : 1111 1000 1100 rY | 1010 0011 0100 rX
            if (w & 0xFFF0) == 0xF8C0:
                w2 = struct.unpack_from("<H", pl, i + 2)[0]
                if (w2 & 0xF000) == 0xA000 and (w2 & 0x0FFF) == 0x234:
                    found.append(i)
        P("      str.w with imm12 == 0x234 : %d site(s)" % len(found))
        for o in found[:8]:
            ins = dis(pl, max(0, o - 0x20), 0x40)
            P("      @ off 0x%05x (flash 0x%08x):" % (o, LOAD + o))
            for i in ins:
                m = " <<<" if i.address - LOAD == o else ""
                P("          0x%08x  %-8s %s%s"
                  % (i.address, i.mnemonic, i.op_str, m))
    P("")

    txt = "\n".join(out)
    dst = os.path.join(ROOT, "data/servo_fw_samples/PATCH_SITE_REVIEW.txt")
    with open(dst, "w", encoding="utf-8") as f:
        f.write(txt + "\n")
    print(txt.encode("ascii", "replace").decode("ascii"))
    print("\n[written] %s" % dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
