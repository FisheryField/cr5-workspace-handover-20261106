#!/usr/bin/env python3
"""Full side-by-side of the position-write block in both builds + gate census.

ESTABLISHED BY tools/servo_patch_audit2.py (per-instruction read of both):
  D8   :  +0x234 = [obj+0xB0] + [X+0x10]
  3150 :  +0x234 = [obj+0xA8] + [X+0x10] + [0x20003DB0+0x18]
                                        ^^^^^^^^^^^^^^^^^^ the only extra term
  and 3150 clears that term to 0 when *(u16*)0x20000020 == 1.

This tool answers the two questions that decide whether the patch is the
right target at all:
  Q1  what does D8's identical block do instead of reading 0x20003DB0 ?
  Q2  who writes 0x20000020 (the gate) and 0x20000022 in either build -
      i.e. is the gate ever satisfied, and is it satisfied in D8 but not 3150 ?
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
WINDOWS = {"D8(3.2.D.8)": (0x154c0, 0x150), "3150(3.1.5.0)": (0x14a20, 0x150)}
GLOBALS = [0x20000020, 0x20000022, 0x20003DB0, 0x20000074, 0x20000078]


def payload(p):
    d = open(p, "rb").read()
    if d[:4] == bytes.fromhex("d4c3b2a1"):
        d = d[0x20:]
    return d


def lit(pl, i, imm):
    a = ((i + 4) & ~3) + imm
    if a + 4 > len(pl):
        return -1
    return struct.unpack_from("<I", pl, a)[0]


def listing(pl, off, n, mark=()):
    md = make_md()
    rows = []
    for i in md.disasm(pl[off:off + n], LOAD + off):
        o = i.address - LOAD
        note = ""
        if "pc" in i.op_str and "#" in i.op_str:
            try:
                imm = int(i.op_str.split("#")[1].rstrip("]"), 0)
                note = "   ; = 0x%08x" % lit(pl, o, imm)
            except Exception:
                pass
        rows.append("  0x%08x (off 0x%05x)  %-9s %-24s%s%s"
                    % (i.address, o, i.mnemonic, i.op_str, note,
                       "  <<<" if o in mark else ""))
    return rows


def census(pl, target):
    """Find instructions that use `target` as a base: literal loads + stores.

    Returns (literal_sites, base_regs) where base_regs maps the register that
    was loaded with the constant, then reports every access through it inside
    the following 12 instructions.
    """
    sites = []
    for i in range(0, len(pl) - 4, 2):
        w = struct.unpack_from("<H", pl, i)[0]
        if (w & 0xF800) != 0x4800:            # 16-bit LDR (literal)
            continue
        rt = (w >> 8) & 7
        if lit(pl, i, ((w & 0xFF) << 2)) != target:
            continue
        sites.append(("LDR", i, rt))
    # Thumb-2 LDR.W (literal) T2: 1111 1000 1101 1111 : Rt : imm12
    for i in range(0, len(pl) - 8, 2):
        w = struct.unpack_from("<H", pl, i)[0]
        if w != 0xF8DF:
            continue
        w2 = struct.unpack_from("<H", pl, i + 2)[0]
        if lit(pl, i, w2 & 0xFFF) != target:
            continue
        sites.append(("LDRW", i, w2 >> 12))
    return sites


def access_report(pl, sites, nmax=14):
    """For each literal load of the constant, list the next few accesses."""
    md = make_md()
    out = []
    for kind, i, rt in sites:
        reg = "r%d" % rt
        body = []
        for ins in md.disasm(pl[i:i + 40], LOAD + i):
            o = ins.address - LOAD
            if o == i:
                continue
            op = ins.op_str
            if op.startswith("[%s]" % reg) or op.startswith("[%s," % reg):
                body.append("        +0x%02x  %-9s %s"
                            % (o - i, ins.mnemonic, op))
            elif (ins.mnemonic.startswith("str") or ins.mnemonic == "strb"
                  or ins.mnemonic.startswith("ldr") or ins.mnemonic == "ldrb"
                  or ins.mnemonic == "ldrh" or ins.mnemonic == "strh"):
                # register may have been copied; keep a loose note
                if reg in op.split(",")[-1] or ("[%s" % reg) in op:
                    body.append("        +0x%02x  %-9s %s" % (o - i, ins.mnemonic, op))
            if len(body) >= nmax:
                break
        out.append((kind, i, reg, body))
    return out


def main():
    out = []
    P = out.append
    P("=" * 78)
    P("Q1  the same block in both builds (position actual value producer)")
    P("=" * 78)
    for name, path in IMAGES.items():
        d = payload(path)
        off, n = WINDOWS[name]
        mark = (0x155ec,) if name.startswith("D8") else (0x14b04, 0x14afe, 0x14b00, 0x14b02)
        P("  --- %s ---" % name)
        out.extend(listing(d, off, n, mark))
        P("")
    P("=" * 78)
    P("Q2  who touches the gate flags / the correction struct")
    P("=" * 78)
    for name, path in IMAGES.items():
        d = payload(path)
        P("  --- %s ---" % name)
        for g in GLOBALS:
            s = census(d, g)
            P("    constant 0x%08x : %d literal-load site(s)" % (g, len(s)))
            for kind, i, rt in s:
                P("        %-4s off 0x%05x (flash 0x%08x)  -> r%d"
                  % (kind, i, LOAD + i, rt))
        P("")

    txt = "\n".join(out)
    dst = os.path.join(ROOT, "data/servo_fw_samples/BLOCK_CMP_GATE.txt")
    with open(dst, "w", encoding="utf-8") as f:
        f.write(txt + "\n")
    print(txt.encode("ascii", "replace").decode("ascii"))
    print("\n[written] %s" % dst)


if __name__ == "__main__":
    main()
