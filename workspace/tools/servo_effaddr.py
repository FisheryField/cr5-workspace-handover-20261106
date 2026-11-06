#!/usr/bin/env python3
"""Resolve EFFECTIVE addresses for every access through a flash literal.

The function-pointer table 0x20000078 (D8) / 0x20000074 (3150) has 36/32 read
sites and ZERO writes when matched by literal value.  But a write could reach it
through a DIFFERENT literal plus an immediate offset - e.g. literal
0x20000064 with store offset +0x14 lands exactly on 0x20000078.

So: for every flash literal pointing anywhere into RAM 0x20000000..0x2001FFFF,
compute base+offset for the first few accesses and report which of them land in
the table block.
"""
import re
import sys
from collections import defaultdict

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image, make_md
from servo_litmap import resolve_literals

CASES = [("D8", "data/servo_fw_samples/elf/v328d8.bin", 0x20000078),
         ("3150", "data/servo_fw_samples/elf/v3150.bin", 0x20000074)]

WRITE_MN = ("str", "strb", "strh", "strd", "vstr", "stm", "stmia", "strex")
READ_MN = ("ldr", "ldrb", "ldrh", "ldrsb", "ldrsh", "ldrd", "vldr", "ldm",
           "ldmia", "ldrex", "tbh", "tbb")

for label, path, tab in CASES:
    lit = resolve_literals(path)
    _r, _h, code = load_image(path)
    md = make_md()
    insns = list(md.disasm(code, FLASH_BASE))
    idx = {i.address: k for k, i in enumerate(insns)}

    # the block we care about: the table and a few slots either side
    lo, hi = tab, tab + 0x60

    print("=" * 76)
    print("BUILD %s : accesses whose EFFECTIVE address lands in 0x%08x..0x%08x"
          % (label, lo, hi))
    print("=" * 76)

    foundw = []
    foundr = []
    for a, (m, o, p, v) in sorted(lit.items()):
        if not (0x20000000 <= v < 0x20020000):
            continue
        reg = o.split(",")[0].strip()
        cur = {reg}
        for j in range(idx[a], min(len(insns), idx[a] + 6)):
            i = insns[j]
            if i.address <= a:
                continue
            mm, oo = i.mnemonic, i.op_str
            if mm in ("mov", "mov.w") and "," in oo:
                d, s = [x.strip() for x in oo.split(",")[:2]]
                if s in cur:
                    cur.add(d)
            if "[" in oo and "pc" not in oo:
                ins = oo.split("[", 1)[1]
                for c in cur:
                    if re.match(r"\s*%s\b" % re.escape(c), ins):
                        offm = re.search(r"#(-?0x[0-9a-f]+)\b", oo)
                        off = int(offm.group(1), 16) if offm else 0
                        eff = v + off
                        if lo <= eff < hi:
                            kind = ("WRITE" if mm in WRITE_MN
                                    else "read " if mm in READ_MN else "?")
                            rec = (i.address, kind, mm, oo, v, off, eff)
                            (foundw if kind == "WRITE" else foundr).append(rec)
            if mm in ("ldr", "add", "sub") and not oo.startswith(reg):
                d = oo.split(",")[0].strip()
                if d in cur and d != reg:
                    cur.discard(d)

    print("  WRITE(s) landing in the table block: %d" % len(foundw))
    for a, kind, mm, oo, v, off, eff in foundw[:20]:
        print("    %08x %-8s %-24s base=0x%08x off=%+#x -> 0x%08x"
              % (a, mm, oo, v, off, eff))
    print()
    print("  reads landing in the table block: %d (sanity; expect many)"
          % len(foundr))
    for a, kind, mm, oo, v, off, eff in foundr[:6]:
        print("    %08x %-8s %-24s base=0x%08x off=%+#x -> 0x%08x"
              % (a, mm, oo, v, off, eff))
    print()
