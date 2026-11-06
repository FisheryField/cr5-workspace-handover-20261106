#!/usr/bin/env python3
"""For every flash literal pointing into 0x20000000..0x20000200, classify the
access as READ or WRITE (and record the immediate offset).

This answers the decisive question for the function-pointer table at 0x20000078
(D8) / 0x20000074 (3150): is ANY of the low-RAM block ever written by an
instruction?  If nothing in the block is written, the whole block must be
initialised by something other than ordinary code (startup copy, debugger,
or a mechanism outside this image).
"""
import re
import sys
from collections import defaultdict

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image, make_md
from servo_litmap import resolve_literals

CASES = [("D8", "data/servo_fw_samples/elf/v328d8.bin"),
         ("3150", "data/servo_fw_samples/elf/v3150.bin")]

WRITE_MN = ("str", "strb", "strh", "strd", "stm", "stmia", "vstr", "strex")
READ_MN = ("ldr", "ldrb", "ldrh", "ldrsb", "ldrsh", "ldrd", "ldm", "ldmia",
           "vldr", "ldrex", "tbh", "tbb")

for label, path in CASES:
    lit = resolve_literals(path)
    _r, _h, code = load_image(path)
    md = make_md()
    insns = list(md.disasm(code, FLASH_BASE))
    idx = {i.address: k for k, i in enumerate(insns)}

    targets = sorted(v for v in {vv for (_m, _o, _p, vv) in lit.values()}
                     if 0x20000000 <= v < 0x20000200)

    print("=" * 76)
    print("BUILD %s : read/write classification for low-RAM block" % label)
    print("=" * 76)

    any_write = False
    for v in targets:
        sites = sorted(a for a, (m, o, p, vv) in lit.items() if vv == v)
        found = defaultdict(list)
        for a in sites:
            reg = lit[a][1].split(",")[0].strip()
            cur = {reg}
            for j in range(idx[a], min(len(insns), idx[a] + 6)):
                i = insns[j]
                if i.address <= a:
                    continue
                m, o = i.mnemonic, i.op_str
                if m in ("mov", "mov.w") and "," in o:
                    d, s = [x.strip() for x in o.split(",")[:2]]
                    if s in cur:
                        cur.add(d)
                if "[" in o and "pc" not in o:
                    ins = o.split("[", 1)[1]
                    for c in cur:
                        if re.match(r"\s*%s\b" % re.escape(c), ins):
                            mm = re.search(r"#(0x[0-9a-f]+)\b", o)
                            off = int(mm.group(1), 16) if mm else 0
                            if m in WRITE_MN:
                                found["WRITE"].append((i.address, m, off))
                            elif m in READ_MN:
                                found["read"].append((i.address, m, off))
        w = found["WRITE"]
        r = found["read"]
        if w:
            any_write = True
        mark = "  <<< WRITE" if w else ""
        print("  0x%08x  read=%2d write=%2d%s" % (v, len(r), len(w), mark))
        for a, m, off in w[:4]:
            print("        %08x %-8s off=0x%x" % (a, m, off))

    print()
    print("  => low-RAM block written by instructions? %s"
          % ("YES" if any_write else "NO - never written in this image"))
    print()
