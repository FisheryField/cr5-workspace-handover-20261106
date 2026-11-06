#!/usr/bin/env python3
"""FINAL ARBITER for the payload load address.

Both payloads share the same first 8 bytes (SP + Reset=0x0801019D), so they MUST
load at the same address.  A Cortex-M reset handler must start with a real
function prologue.  So: disassemble at BOTH candidate offsets in BOTH payloads and
see which candidate yields sane code in both.

  load = 0x08000000  ->  Reset at payload offset 0x1019C
  load = 0x08010000  ->  Reset at payload offset 0x0019C
"""
import struct
import sys

sys.path.insert(0, "tools")
from servo_img import make_md

md = make_md()
CASES = [("D8", "data/servo_fw_samples/elf/v328d8.bin"),
         ("3150", "data/servo_fw_samples/elf/v3150.bin")]

for label, path in CASES:
    pl = open(path, "rb").read()
    print("=" * 74)
    print("%s  payload %d B" % (label, len(pl)))
    print("=" * 74)
    for load in (0x08000000, 0x08010000):
        off = 0x0801019C - load
        if off + 16 > len(pl):
            print("  load=0x%08x : Reset offset 0x%x OUT OF RANGE" % (load, off))
            continue
        print("  load=0x%08x -> Reset at payload offset 0x%05x:" % (load, off))
        for i in md.disasm(pl[off:off + 16], 0x0801019C):
            print("       %08x  %-10s %-24s size=%d" % (i.address, i.mnemonic, i.op_str, i.size))
    print()
    # sanity: what is AT each candidate offset
    print("  payload offset 0x00000: %s" % pl[:16].hex(" "))
    print("  payload offset 0x0001C: %s" % pl[0x1C:0x2C].hex(" "))
    print("  payload offset 0x10000: %s" % (pl[0x10000:0x10010].hex(" ") if len(pl) > 0x10010 else "n/a"))
    print()
