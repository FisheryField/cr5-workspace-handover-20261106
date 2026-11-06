#!/usr/bin/env python3
"""Chain-line comparison: accesses to descriptor fields reached ONLY through the
descriptor-array base literal (0x2000138C D8 / 0x2000129C 3150).

Bare `[rX,#off]` counts are useless here: +0x14/+0x10/+0x20 etc. occur hundreds of
times as STACK accesses.  So restrict to accesses reachable from a literal load of
the descriptor base, tracking the base register forward a few instructions (and
through one `mov`).

Reports, per field, the write sites in each build so the +0x14 (reference
position) and +0x1C (deviation) lines can be compared line by line.
"""
import re
import sys

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image, make_md
from servo_litmap import resolve_literals

CASES = [("D8", "data/servo_fw_samples/elf/v328d8.bin", 0x2000138C),
         ("3150", "data/servo_fw_samples/elf/v3150.bin", 0x2000129C)]

FIELDS = [0x10, 0x14, 0x18, 0x1C, 0x20, 0x24, 0x28, 0x30, 0x36, 0x238, 0x230, 0x234]

WRITE = ("str", "strb", "strh", "vstr", "strd")
READ = ("ldr", "ldrb", "ldrh", "vldr", "ldrsh", "ldrsb")


def scan(path, base):
    _r, _h, code = load_image(path)
    md = make_md()
    insns = list(md.disasm(code, FLASH_BASE))
    idx = {i.address: k for k, i in enumerate(insns)}
    lit = resolve_literals(path)
    sites = sorted(a for a, (m, o, p, v) in lit.items() if v == base)

    out = {f: {"W": [], "R": []} for f in FIELDS}
    WANT = set(FIELDS)
    for a in sites:
        reg = lit[a][1].split(",")[0].strip()
        cur = {reg}
        for j in range(idx[a], min(len(insns), idx[a] + 8)):
            i = insns[j]
            if i.address <= a:
                continue
            m, o = i.mnemonic, i.op_str
            if m in ("mov", "mov.w") and "," in o:
                d, s = [x.strip() for x in o.split(",")[:2]]
                if s in cur:
                    cur.add(d)
                    continue
            if "[" in o and "pc" not in o and "sp" not in o:
                inside = o.split("[", 1)[1]
                for c in cur:
                    if not re.match(r"\s*%s\b" % re.escape(c), inside):
                        continue
                    mm = re.search(r"#(0x[0-9a-f]+)\]", o)
                    if not mm:
                        continue
                    off = int(mm.group(1), 16)
                    if off in WANT:
                        kind = "W" if m in WRITE else ("R" if m in READ else None)
                        if kind:
                            out[off][kind].append((i.address, m, o))
            if (m.startswith("ldr") or m.startswith("add") or m.startswith("sub")):
                d = o.split(",")[0].strip()
                if d in cur and d != reg:
                    cur.discard(d)
    return out


A = scan(CASES[0][1], CASES[0][2])
B = scan(CASES[1][1], CASES[1][2])

print("field   | D8 W/R      | 3150 W/R    | D8 write sites")
print("-" * 76)
for f in FIELDS:
    aw, ar = len(A[f]["W"]), len(A[f]["R"])
    bw, br = len(B[f]["W"]), len(B[f]["R"])
    flag = "  <<< DIFFERS" if (aw, ar) != (bw, br) else ""
    print("+0x%03x  | W=%-3d R=%-3d | W=%-3d R=%-3d |%s"
          % (f, aw, ar, bw, br, flag))
    for a, m, o in A[f]["W"][:6]:
        print("              %08x %-9s %s" % (a, m, o))
print()
print("=== 3150 write sites for the differing fields ===")
for f in FIELDS:
    if len(A[f]["W"]) != len(B[f]["W"]) or len(A[f]["R"]) != len(B[f]["R"]):
        print("+0x%03x :" % f)
        for a, m, o in B[f]["W"][:8]:
            print("    %08x %-9s %s" % (a, m, o))
