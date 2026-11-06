#!/usr/bin/env python3
"""Read out, instruction by instruction, every use of D8's 0x20003EF8.

tools/servo_global_role.py returned an EMPTY field tally for this base, which is
the classic silent-failure signature in this workspace (see AGENTS.md: five
distinct classes of "tool returns 0 and does not say so").  So the sites are
dumped raw here instead of being summarised.  The question being answered:
does D8's counterpart struct ALSO carry a correction term, applied somewhere
other than the +0x234 line that was read byte by byte?
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from servo_img import make_md  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D8 = os.path.join(ROOT, "data/servo_fw_samples/elf/v328d8.bin")
V3150 = os.path.join(ROOT, "data/servo_fw_samples/elf/v3150.bin")
LOAD = 0x08010000


def payload(p):
    d = open(p, "rb").read()
    if d[:4] == bytes.fromhex("d4c3b2a1"):
        d = d[0x20:]
    return d


def lit(pl, i, imm):
    a = ((i + 4) & ~3) + imm
    return struct.unpack_from("<I", pl, a)[0] if a + 4 <= len(pl) else -1


def sites(pl, target):
    md = make_md()
    out = []
    for ins in md.disasm(pl, LOAD):
        if ins.mnemonic.startswith("ldr") and "[pc" in ins.op_str:
            try:
                imm = int(ins.op_str.split("#")[1].split("]")[0].strip(), 0)
            except Exception:
                continue
            if lit(pl, ins.address - LOAD, imm) == target:
                out.append(ins.address)
    return out


def dump(pl, addr, back=0, fwd=10):
    md = make_md()
    o = addr - LOAD
    rows = []
    for ins in md.disasm(pl[max(0, o - back):o + fwd * 4], LOAD + max(0, o - back)):
        mark = " <<<" if ins.address == addr else ""
        rows.append("      0x%08x  %-9s %-26s%s"
                    % (ins.address, ins.mnemonic, ins.op_str, mark))
    return rows


def main():
    out = []
    P = out.append
    for name, path, tgt in (("D8 / 0x20003ef8", D8, 0x20003EF8),
                            ("3150 / 0x20003db0", V3150, 0x20003DB0)):
        pl = payload(path)
        s = sites(pl, tgt)
        P("=" * 78)
        P("%s : %d literal-load site(s)" % (name, len(s)))
        P("=" * 78)
        for a in s:
            P("  --- site 0x%08x ---" % a)
            out.extend(dump(pl, a))
        P("")

    txt = "\n".join(out)
    dst = os.path.join(ROOT, "data/servo_fw_samples/EF8_SITES.txt")
    with open(dst, "w", encoding="utf-8") as f:
        f.write(txt + "\n")
    # console: D8 only (that is what is under question)
    cut = txt.split("3150 / 0x20003db0")[0]
    print(cut.encode("ascii", "replace").decode("ascii"))
    print("\n[full listing of both] %s" % dst)


if __name__ == "__main__":
    main()
