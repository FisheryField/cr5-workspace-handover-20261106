#!/usr/bin/env python3
"""Find the engine side of the OD field-pointer handshake.

Established: every OD dispatcher handler ends with
    str r3,[r0,#0x18]        ; publish &descriptor[axis].field
followed by `b <common tail>`.  The core engine must therefore read that
pointer back with `ldr rY,[rX,#0x18]` and then use rY as a pointer - that is the
single funnel through which ALL OD field values (including Homing method 0x6098)
reach the logic that consumes them.

This script finds every `ldr rY,[rX,#0x18]` whose result is then dereferenced or
passed as a pointer, i.e. the handshake consumers.
"""
import re
import sys

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image, make_md

CASES = [("D8", "data/servo_fw_samples/elf/v328d8.bin"),
         ("3150", "data/servo_fw_samples/elf/v3150.bin")]

for label, path in CASES:
    _r, _h, code = load_image(path)
    md = make_md()
    insns = list(md.disasm(code, FLASH_BASE))
    idx = {i.address: k for k, i in enumerate(insns)}

    print("=" * 78)
    print("BUILD %s : `ldr rY,[rX,#0x18]` handshake consumers" % label)
    print("=" * 78)

    cand = []
    for i in insns:
        if i.mnemonic != "ldr":
            continue
        m = re.match(r"(r\d+|ip|sl|fp|sb), \[(r\d+|ip|sl|fp|sb), #0x18\]$", i.op_str)
        if m:
            cand.append((i.address, m.group(1), m.group(2)))

    print("  %d candidate ldr [..,#0x18] sites" % len(cand))
    consumer = []
    for a, dst, base in cand:
        k = idx[a]
        for j in range(k + 1, min(len(insns), k + 8)):
            x = insns[j]
            o = x.op_str
            # used as a base register, or dereferenced
            if re.search(r"\[%s\b" % re.escape(dst), o) or \
               re.search(r"\b%s\b" % re.escape(dst), o) and x.mnemonic in ("blx", "bx", "ldr", "str"):
                consumer.append((a, dst, base, x.address, x.mnemonic, o))
                break
            if x.mnemonic.startswith(("b", "pop")) and x.mnemonic != "blx":
                break

    print("  %d of them are consumed as a pointer/argument" % len(consumer))
    for a, dst, base, ua, um, uo in consumer[:40]:
        print("     %08x ldr %s,[%s,#0x18]  ->  %08x %-8s %s"
              % (a, dst, base, ua, um, uo))
    print()
