#!/usr/bin/env python3
"""Locate block-copy loops (load/store pairs inside small backward branches).

A startup copy of initialised data (flash -> RAM) compiles to a tight loop
containing both a load and a store, closed by a short backward branch.  Finding
those loops and reporting the addresses each one touches lets us see whether
anything copies initialised data into the low RAM block 0x20000000..0x20000200
(where the never-written function-pointer table at 0x20000078 lives).
"""
import re
import sys

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image, make_md
from servo_litmap import resolve_literals

CASES = [("D8", "data/servo_fw_samples/elf/v328d8.bin"),
         ("3150", "data/servo_fw_samples/elf/v3150.bin")]

WRITE_MN = ("str", "strb", "strh", "vstr", "stm", "stmia")
READ_MN = ("ldr", "ldrb", "ldrh", "vldr", "ldm", "ldmia")


for label, path in CASES:
    _r, _h, code = load_image(path)
    md = make_md()
    insns = list(md.disasm(code, FLASH_BASE))
    lit = resolve_literals(path)

    print("=" * 76)
    print("BUILD %s : block-copy candidate loops" % label)
    print("=" * 76)

    found = 0
    for k, i in enumerate(insns):
        if i.mnemonic not in ("b", "bne", "bgt", "blt", "bge", "ble", "bls", "bhi", "bhs", "blo"):
            continue
        m = re.match(r"#(0x[0-9a-f]+)", i.op_str)
        if not m:
            continue
        tgt = int(m.group(1), 16)
        if not (0 < i.address - tgt <= 0x60):      # short backward branch
            continue
        # does the loop body contain both a load and a store?
        body = [x for x in insns if tgt <= x.address <= i.address]
        has_l = any(x.mnemonic in READ_MN for x in body)
        has_s = any(x.mnemonic in WRITE_MN for x in body)
        if not (has_l and has_s):
            continue
        found += 1
        # collect literal targets referenced in the body + any low-RAM addresses
        lits = sorted({lit[x.address][3] for x in body if x.address in lit})
        lowram = [v for v in lits if 0x20000000 <= v < 0x20000200]
        flashsrc = [v for v in lits if 0x08000000 <= v < 0x08100000]
        tag = ""
        if lowram:
            tag = "  <<< touches low RAM %s" % [hex(v) for v in lowram]
        print("   loop %08x..%08x (%d insn)  lits=%s%s"
              % (tgt, i.address, len(body),
                 " ".join(hex(v) for v in lits[:6]), tag))
        if len(lits) > 6:
            print("        more lits: %s" % " ".join(hex(v) for v in lits[6:16]))
    print("   total candidate loops: %d" % found)
    print()
