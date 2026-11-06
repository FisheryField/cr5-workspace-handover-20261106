#!/usr/bin/env python3
"""Census (fast): per-axis descriptor field write/read counts, both builds.

Disassembles each image ONCE, then counts accesses per offset.  Reports the
D8-vs-3150 pairs whose (writes, reads) differ - those are concrete structural
differences worth reading.

CENSUS ONLY: may shortlist candidates, never conclude.
"""
import re
import sys
from collections import defaultdict

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image, make_md
from servo_litmap import resolve_literals

PAIRS = [
    (0x13E, 0x13E), (0x140, 0x140), (0x142, 0x142), (0x144, 0x144),
    (0x146, 0x146), (0x148, 0x148), (0x14A, 0x14A), (0x14C, 0x14C),
    (0x14D, 0x14D), (0x1AE, 0x1AE), (0x1AF, 0x1AF), (0x1B3, 0x1B3),
    (0x1BD, 0x1BD), (0x1C7, 0x1C7), (0x1CB, 0x1CB), (0x1CF, 0x1CF),
    (0x1D3, 0x1D3), (0x1D7, 0x1D7), (0x1DB, 0x1DB), (0x1DF, 0x1DF),
    (0x1E3, 0x1E3), (0x1E5, 0x1E5), (0x1E6, 0x1E6),
    (0x200, 0x200), (0x204, 0x204), (0x208, 0x208),
    (0x20C, 0x1F4), (0x20D, 0x1F5), (0x217, 0x1FF), (0x21B, 0x203),
    (0x21D, 0x205), (0x220, 0x208), (0x224, 0x20C), (0x228, 0x210),
    (0x22C, 0x214), (0x230, 0x218), (0x234, 0x21C), (0x238, 0x220),
    (0x23C, 0x224), (0x240, 0x228), (0x242, 0x22A), (0x246, 0x22E),
    (0x248, 0x230), (0x24C, 0x234), (0x250, 0x238), (0x26A, 0x252),
    (0x26E, 0x256), (0x270, 0x258), (0x272, 0x25A), (0x29C, 0x284),
    (0x2A0, 0x288), (0x2A4, 0x2A4), (0x2B3, 0x29B), (0x2B7, 0x29F),
    (0x2B9, 0x2A1), (0x2BD, 0x2A5), (0x2C1, 0x2A9), (0x2C3, 0x2AB),
    (0x2C5, 0x2AD), (0x2C7, 0x2AF), (0x2C9, 0x2B1), (0x2CD, 0x2B5),
    (0x2D1, 0x2B9), (0x2DD, 0x2C5), (0x2DF, 0x2C7), (0x2E1, 0x2C9),
    (0x2E3, 0x2CB), (0x2E5, 0x2CD), (0x2E9, 0x2D1), (0x2ED, 0x2D5),
    (0x2EF, 0x2D7), (0x2F1, 0x2D9),
    (0xA4, 0xA4), (0xA8, 0xA8), (0xAC, 0xAC), (0xB0, 0xB0), (0xB4, 0xB4),
    (0x9C, 0x9C), (0x30, 0x30), (0x20, 0x20), (0x14, 0x14), (0x18, 0x18),
    (0x1C, 0x1C), (0x24, 0x24), (0x34, 0x34), (0x36, 0x36), (0x48, 0x48),
    (0x50, 0x50), (0x60, 0x60), (0x64, 0x64), (0x68, 0x68),
]

WRITE_MN = ("str", "strb", "strh", "vstr", "strd", "stm")
READ_MN = ("ldr", "ldrb", "ldrh", "vldr", "ldrsh", "ldrsb", "ldm")


def build_counts(path, base):
    """Return {offset: [writes, reads]} for accesses provably on the descriptor."""
    _r, _h, code = load_image(path)
    md = make_md()
    insns = list(md.disasm(code, FLASH_BASE))
    idx = {i.address: k for k, i in enumerate(insns)}
    lit = resolve_literals(path)
    base_sites = [a for a, (m, o, p, v) in lit.items() if v == base]

    want = set()
    for oa, ob in PAIRS:
        want.add(oa)
        want.add(ob)

    cnt = defaultdict(lambda: [0, 0])
    # (a) direct [rX,#off]
    for i in insns:
        if "pc" in i.op_str or "sp" in i.op_str:
            continue
        for off in want:
            if re.search(r"#0x%x\]" % off, i.op_str):
                if i.mnemonic in WRITE_MN:
                    cnt[off][0] += 1
                elif i.mnemonic in READ_MN:
                    cnt[off][1] += 1
    # (b) through the descriptor base literal
    for a in base_sites:
        reg = lit[a][1].split(",")[0].strip()
        cur = {reg}
        for j in range(idx[a], min(len(insns), idx[a] + 5)):
            i = insns[j]
            if i.address <= a:
                continue
            if i.mnemonic in ("mov", "mov.w") and "," in i.op_str:
                d, sm = [x.strip() for x in i.op_str.split(",")[:2]]
                if sm in cur:
                    cur.add(d)
            if "[" in i.op_str and "pc" not in i.op_str and "sp" not in i.op_str:
                ins = i.op_str.split("[", 1)[1]
                for c in cur:
                    if re.match(r"\s*%s\b" % re.escape(c), ins):
                        for off in want:
                            if re.search(r"#0x%x\]" % off, i.op_str):
                                if i.mnemonic in WRITE_MN:
                                    cnt[off][0] += 1
                                elif i.mnemonic in READ_MN:
                                    cnt[off][1] += 1
    return cnt


A = build_counts("data/servo_fw_samples/elf/v328d8.bin", 0x2000138C)
B = build_counts("data/servo_fw_samples/elf/v3150.bin", 0x2000129C)
print("offsets counted: D8=%d  3150=%d" % (len(A), len(B)))
print()
print("%-8s %-8s | %-12s | %-12s | %s" % ("D8", "3150", "D8 W/R", "3150 W/R", "flag"))
print("-" * 62)
ndiff = 0
for oa, ob in PAIRS:
    wa, ra = A.get(oa, [0, 0])
    wb, rb = B.get(ob, [0, 0])
    flag = ""
    if (wa, ra) != (wb, rb):
        flag = "  <<< DIFFERS"
        ndiff += 1
    print("0x%03X    0x%03X    | W=%-3d R=%-4d | W=%-3d R=%-4d |%s"
          % (oa, ob, wa, ra, wb, rb, flag))
print()
print("pairs differing: %d / %d" % (ndiff, len(PAIRS)))
