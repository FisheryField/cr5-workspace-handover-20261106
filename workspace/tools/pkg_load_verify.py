#!/usr/bin/env python3
"""Re-verify which flash address each servo package payload belongs at.

Method (measurement, not inference): for each package, decode the payload at
successive candidate offsets and check the Cortex-M vector-table invariants:
  * dword 0 is a plausible SRAM stack pointer
  * dword 1 is an odd (Thumb) address inside the image
Then disassemble at the Reset vector and check it decodes to sane code.

This matters because the earlier conclusion "payload loads at 0x08000000" was
inferred from the first dword alone, and a full-length match against 3.1.5.hex
later showed the 3.1.5.0 payload actually belongs at 0x08010000.
"""
import struct
import sys

sys.path.insert(0, "tools")
from servo_img import make_md

CASES = [("D8  (v328d8.bin)", "data/servo_fw_samples/elf/v328d8.bin"),
         ("3150 (v3150.bin)", "data/servo_fw_samples/elf/v3150.bin")]

md = make_md()

for label, path in CASES:
    raw = open(path, "rb").read()
    print("=" * 74)
    print("%s   file size %d" % (label, len(raw)))
    print("=" * 74)
    for hdr in (0, 0x20):
        pl = raw[hdr:]
        sp = struct.unpack_from("<I", pl, 0)[0]
        rv = struct.unpack_from("<I", pl, 4)[0]
        print("  header offset 0x%02x -> payload %d B" % (hdr, len(pl)))
        print("     dword0 = 0x%08x  (SRAM SP? %s)"
              % (sp, "yes" if 0x20000000 <= sp < 0x20080000 else "no"))
        if (rv & 1) == 1 and 0x08000000 <= (rv & ~1) < 0x08200000:
            print("     dword1 = 0x%08x  (Thumb addr in flash: yes)" % rv)
            # if the payload sits at LOAD, then dword1 refers to flash address rv
            # which must fall inside the payload's own range [LOAD, LOAD+len)
            for load in (0x08000000, 0x08010000):
                inside = load <= (rv & ~1) < load + len(pl)
                off = (rv & ~1) - load
                ok = ""
                if 0 <= off < len(pl):
                    ins = list(md.disasm(pl[off:off + 2], rv & ~1))
                    ok = "decodes: %s %s" % (ins[0].mnemonic, ins[0].op_str) if ins else "no decode"
                print("        if load=0x%08x : Reset inside payload = %-5s  %s"
                      % (load, inside, ok))
        else:
            print("     dword1 = 0x%08x  (NOT a Thumb flash addr)" % rv)
    print()
