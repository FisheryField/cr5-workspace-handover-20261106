#!/usr/bin/env python3
"""Byte-accurate instruction map around the 3150 patch site.

Prints each instruction with its exact byte offset, raw bytes and size, so a
byte-patch can be specified unambiguously.  (My first attempt used addresses
derived from a listing that skipped 4-byte instructions, so the offsets were
wrong: several instructions in this region are 16-bit encodings.)
"""
import sys

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image, make_md

CASES = [("3150", "data/servo_fw_samples/elf/v3150.bin", 0x08014AE0, 0x08014B20),
         ("D8", "data/servo_fw_samples/elf/v328d8.bin", 0x080155C0, 0x08015610)]

for label, path, lo, hi in CASES:
    _r, _h, code = load_image(path)
    md = make_md()
    print("=" * 78)
    print("BUILD %s : byte map 0x%08x..0x%08x" % (label, lo, hi))
    print("=" * 78)
    for i in md.disasm(code[lo - FLASH_BASE:hi - FLASH_BASE], lo):
        rawb = code[i.address - FLASH_BASE:i.address - FLASH_BASE + i.size]
        print("  %08x  %-6s %-22s size=%d  bytes=%s"
              % (i.address, i.mnemonic, i.op_str, i.size, rawb.hex(" ")))
    print()
