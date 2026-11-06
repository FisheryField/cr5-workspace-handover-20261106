#!/usr/bin/env python3
"""Read the gate block in D8 (its own 0x20000020 sites) to see whether D8
enables/disables the SAME kind of correction, and with which flag byte.

Context: in 3150 the position line is
    +0x234 = normalize + obj->0x10 + [0x20003DB0+0x18]
and [0x20003DB0+0x18] is forced to 0 when *(u16*)0x20000020 == 1.
D8's position line has no third term at all.  D8 also reads 0x20000020
(0x080253E8, 0x080253F8) - so what does D8's copy of this block look like?
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from servo_img import make_md  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES = {
    "D8": (os.path.join(ROOT, "data/servo_fw_samples/elf/v328d8.bin"),
           [(0x153c0, 0x110), (0x18d40, 0x60)]),
    "3150": (os.path.join(ROOT, "data/servo_fw_samples/elf/v3150.bin"),
             [(0x15be0, 0xc0), (0x18850, 0x60), (0x2ef60, 0x60)]),
}
LOAD = 0x08010000


def payload(p):
    d = open(p, "rb").read()
    if d[:4] == bytes.fromhex("d4c3b2a1"):
        d = d[0x20:]
    return d


def lit(pl, i, imm):
    a = ((i + 4) & ~3) + imm
    return struct.unpack_from("<I", pl, a)[0] if a + 4 <= len(pl) else -1


def dump(pl, off, n):
    md = make_md()
    rows = []
    for ins in md.disasm(pl[off:off + n], LOAD + off):
        o = ins.address - LOAD
        note = ""
        if ins.mnemonic.startswith("ldr") and "[pc" in ins.op_str:
            try:
                imm = int(ins.op_str.split("#")[1].split("]")[0].strip(), 0)
                note = "   ; = 0x%08x" % lit(pl, o, imm)
            except Exception:
                pass
        rows.append("    0x%08x (off 0x%05x)  %-9s %-26s%s"
                    % (ins.address, o, ins.mnemonic, ins.op_str, note))
    return rows


def main():
    out = []
    for name, (path, wins) in IMAGES.items():
        pl = payload(path)
        out.append("=" * 78)
        out.append("%s   gate / position block" % name)
        out.append("=" * 78)
        for off, n in wins:
            out.append("  --- offset 0x%05x ---" % off)
            out.extend(dump(pl, off, n))
            out.append("")

    txt = "\n".join(out)
    dst = os.path.join(ROOT, "data/servo_fw_samples/GATE_BLOCKS.txt")
    with open(dst, "w", encoding="utf-8") as f:
        f.write(txt + "\n")
    print(txt.encode("ascii", "replace").decode("ascii"))
    print("\n[written] %s" % dst)


if __name__ == "__main__":
    main()
