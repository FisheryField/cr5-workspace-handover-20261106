#!/usr/bin/env python3
"""Second pass: dump the literal pool at the patch site and compare both builds.

Two defects in the previous pass, both fixed here:
  * the `str.w ...,#0x234` search masked the second halfword wrong
    (Thumb-2 STR imm T4 is `1111 1000 1100 Rn : Rt : imm12`, so the test is
    `(w2 & 0xFFF) == 0x234`, with Rt in bits 15..12 - not `(w2 & 0xF000)==0xA000`)
  * the literal-pool values were never read, so the base of `[r1,#0x18]` was
    only assumed
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from servo_img import make_md  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES = {
    "D8(3.2.D.8)": os.path.join(ROOT, "data/servo_fw_samples/elf/v328d8.bin"),
    "3150(3.1.5.0)": os.path.join(ROOT, "data/servo_fw_samples/elf/v3150.bin"),
}
LOAD = 0x08010000


def payload(p):
    d = open(p, "rb").read()
    if d[:4] == bytes.fromhex("d4c3b2a1"):
        d = d[0x20:]
    return d


def lit16(pl, i, imm):
    """Thumb LDR (literal) base = Align(PC,4), PC = i+4."""
    return struct.unpack_from("<I", pl, ((i + 4) & ~3) + imm)[0]


def dis(pl, off, n):
    md = make_md()
    return list(md.disasm(pl[off:off + n], LOAD + off))


def find_str_234(pl):
    hits = []
    for i in range(0, len(pl) - 4, 2):
        w = struct.unpack_from("<H", pl, i)[0]
        if (w & 0xFFF0) != 0xF8C0:
            continue
        w2 = struct.unpack_from("<H", pl, i + 2)[0]
        if (w2 & 0x0FFF) == 0x234:
            hits.append((i, w & 0xF, w2 >> 12))
    return hits


def main():
    out = []
    P = out.append
    pl = {}

    P("=" * 78)
    P("A. every `str.w rX,[rY,#0x234]` in both builds")
    P("=" * 78)
    for name, path in IMAGES.items():
        d = payload(path)
        pl[name] = d
        h = find_str_234(d)
        P("  %s : %d site(s)" % (name, len(h)))
        for off, rn, rt in h:
            P("      off 0x%05x  flash 0x%08x   str.w r%d,[r%d,#0x234]"
              % (off, LOAD + off, rt, rn))
    P("")

    # ---- literal pool of the 3150 site ----
    P("=" * 78)
    P("B. 3150 literal pool used by the patch block")
    P("=" * 78)
    v = pl["3150(3.1.5.0)"]
    for i, imm in ((0x14afe, 0xb0), (0x14b1a, 0x94), (0x14b2c, 0x80),
                   (0x14b3e, 0x70), (0x14b52, 0x5c), (0x14b5a, 0x58),
                   (0x14ae2, 0xb4), (0x14ae6, 0xc4), (0x14af0, 0xbc)):
        a = ((i + 4) & ~3) + imm
        P("  insn off 0x%05x (ldr pc,#0x%02x) -> literal flash 0x%08x = 0x%08x"
          % (i, imm, LOAD + a, lit16(v, i, imm)))
    P("")

    P("=" * 78)
    P("C. the patch block in 3150, with literals resolved")
    P("=" * 78)
    for i in dis(v, 0x14ae0, 0x40):
        o = i.address - LOAD
        note = ""
        if i.mnemonic.startswith("ldr") and "[pc" in i.op_str:
            try:
                imm = int(i.op_str.split("#")[1].rstrip("]"), 0)
                note = "   ; = 0x%08x" % lit16(v, o, imm)
            except Exception:
                pass
        P("  0x%08x (off 0x%05x)  %-8s %-22s%s"
          % (i.address, o, i.mnemonic, i.op_str, note))
    P("")
    P("  >>> r0 at 0x08024afc = [sp+0x14]->+0x10  +  [r5+0xA8]")
    P("  >>> r1 at 0x08024b02 = [<literal>+0x18]  (the 'correction')")
    P("  >>> 0x08024b04 stores **r1** into +0x234")
    P("  >>> to make +0x234 == r0 the patch must be `mov r1, r0` = 01 46")
    P("")

    # ---- D8 counterpart ----
    P("=" * 78)
    P("D. D8 counterpart block")
    P("=" * 78)
    d8 = pl["D8(3.2.D.8)"]
    h8 = find_str_234(d8)
    if not h8:
        P("  no str.w ...#0x234 site in D8 at all")
    for off, rn, rt in h8:
        P("  --- site off 0x%05x (flash 0x%08x) ---" % (off, LOAD + off))
        for i in dis(d8, max(0, off - 0x40), 0x60):
            o = i.address - LOAD
            note = ""
            if i.mnemonic.startswith("ldr") and "[pc" in i.op_str:
                try:
                    imm = int(i.op_str.split("#")[1].rstrip("]"), 0)
                    note = "   ; = 0x%08x" % lit16(d8, o, imm)
                except Exception:
                    pass
            m = " <<<" if o == off else ""
            P("      0x%08x (off 0x%05x)  %-8s %-22s%s%s"
              % (i.address, o, i.mnemonic, i.op_str, note, m))
    P("")

    # ---- is the 3150 correction-read shape present in D8? ----
    P("=" * 78)
    P("E. does D8 contain the `ldr r1,[r1,#0x18]` + `add r1,r0` shape at all?")
    P("=" * 78)
    shape = bytes.fromhex("89690144")   # ldr r1,[r1,#0x18] ; add r1,r0
    for name, d in pl.items():
        hits = []
        i = d.find(shape)
        while i >= 0:
            hits.append(i)
            i = d.find(shape, i + 1)
        P("  %s : %d occurrence(s) of %s" % (name, len(hits), shape.hex(" ")))
        for h in hits:
            P("      off 0x%05x (flash 0x%08x)" % (h, LOAD + h))
    P("")

    txt = "\n".join(out)
    dst = os.path.join(ROOT, "data/servo_fw_samples/PATCH_SITE_REVIEW2.txt")
    with open(dst, "w", encoding="utf-8") as f:
        f.write(txt + "\n")
    print(txt.encode("ascii", "replace").decode("ascii"))
    print("\n[written] %s" % dst)


if __name__ == "__main__":
    main()
