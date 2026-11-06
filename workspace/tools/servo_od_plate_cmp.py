#!/usr/bin/env python3
"""Compare the OD dispatcher's descriptor-offset table between the two builds.

Produces, for each build, the ORDERED list of (handler_addr, descriptor offset)
as it appears in the dispatcher, then aligns the two lists positionally.

Why positional alignment is legitimate here: the handlers are emitted as one
contiguous run of identical 8-instruction stubs in dispatcher order, and the OD
metadata table (97 records) is identical between builds in content AND order
(established earlier, tools/servo_od_names_cmp.py).  So plate i of build A
corresponds to plate i of build B, and any offset difference is a real structural
shift rather than a reordering.
"""
import re
import sys

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image, make_md
from servo_litmap import resolve_literals

CASES = [("D8", "data/servo_fw_samples/elf/v328d8.bin"),
         ("3150", "data/servo_fw_samples/elf/v3150.bin")]
STRIDE = 0x329


def plate_list(path):
    _r, _h, code = load_image(path)
    md = make_md()
    insns = list(md.disasm(code, FLASH_BASE))
    lit = resolve_literals(path)
    out = []
    for k, ins in enumerate(insns):
        if ins.mnemonic != "movw" or not re.search(r"#0x%x\b" % STRIDE, ins.op_str):
            continue
        off = base = None
        for j in range(k, min(len(insns), k + 8)):
            a, m, o = insns[j].address, insns[j].mnemonic, insns[j].op_str
            if a in lit:
                base = lit[a][3]
            mm = re.search(r"#(0x[0-9a-f]+)\b", o)
            if m in ("addw", "add.w", "add") and "r3" in o and mm:
                off = int(mm.group(1), 16)
        if off is not None:
            out.append((ins.address, base, off))
    return out


a = plate_list(CASES[0][1])
b = plate_list(CASES[1][1])
print("D8 plates: %d    3150 plates: %d" % (len(a), len(b)))
print()

# filter to the descriptor array base only (drop the single 0x20000114 outlier)
def filt(lst, want):
    return [t for t in lst if t[1] == want]

# discover each build's dominant base
from collections import Counter
base_a = Counter(t[1] for t in a).most_common(1)[0][0]
base_b = Counter(t[1] for t in b).most_common(1)[0][0]
print("dominant base  D8=0x%08x  3150=0x%08x" % (base_a, base_b))
fa, fb = filt(a, base_a), filt(b, base_b)
print("plates on dominant base: D8=%d  3150=%d" % (len(fa), len(fb)))
print()

n = min(len(fa), len(fb))
same = diff = 0
print(" idx   D8 off  D8 handler   3150 off  3150 handler   delta")
for i in range(n):
    oa, ob = fa[i][2], fb[i][2]
    d = ob - oa
    tag = "same" if d == 0 else "%+d" % d
    if d == 0:
        same += 1
    else:
        diff += 1
    print(" %3d   0x%03x   %08x     0x%03x    %08x    %s"
          % (i, oa, fa[i][0], ob, fb[i][0], tag))

print()
print("offsets identical: %d   differing: %d" % (same, diff))
deltas = Counter(fb[i][2] - fa[i][2] for i in range(n))
print("delta histogram: %s" % dict(deltas))
