#!/usr/bin/env python3
"""Search both servo builds for CiA402 object indices, correctly.

BUG THAT MOTIVATED THIS FILE (found this session):
  A previous inline scanner tested `(w1 & 0x7) << 12` for the `imm3` field of
  Thumb-2 `movw`, but `imm3` actually lives in bits 12..14, so the correct mask
  is `0x7000`.  Every 32-bit constant decoded as a tiny number and therefore
  never matched.  The bug was caught only because a *positive control*
  (`movw r1,#0x4e20` at 0x080155A6) returned 0 sites.
  => Any earlier "index not present in the image" claim from that code is VOID.

Encodings covered (Thumb-2, 32-bit):
  movw  rX, #imm16   : 11110 i 10 0100 imm4 | 0 imm3 Rd imm8
  movt  rX, #imm16   : 11110 i 10 1100 imm4 | 0 imm3 Rd imm8
  -> a 32-bit constant is usually armed as movw(lo) + movt(hi); this firmware
     does NOT emit adjacent pairs (movw 459 / movt 40 / pairs 0), so a plain
     16-bit movw match is the strongest available signal.
"""
import re
import sys

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image, make_md

TARGETS = [0x607C, 0x6098, 0x6063, 0x6064, 0x6060, 0x6040, 0x6041, 0x6061]
CONTROLS = [0x4E20, 0x20000, 0x329, 0xE4, 0x64, 0x164]   # 0x4E20 already proven present


def imm16_sites(code, val):
    """All movw/movt sites whose 16-bit immediate == val.

    Encoding (verified byte-by-byte against capstone on 0x080155A6 = f6 44 20 61
    -> `movw r1, #0x4e20`):
        w1 = 11110 i 10 <op4> imm4       op4 = 0b0100 movw / 0b1100 movt
        w2 = 0 imm3 Rd imm8
        imm16 = imm4:i:imm3:imm8
    Two bugs were found here the hard way:
      * the `i` bit is 1 in this encoding, not 0 (I asserted 0 -> every site
        rejected).  The Thumb-2 "i" bit is *not* an immediate's high bit
        polarity check; it simply participates as bit 11 of imm16.
      * `imm3` lives in w2 bits 14..12 (mask 0x7000), not w1 bits 14..12.
    """
    out = []
    for o in range(0, len(code) - 4, 2):
        w1 = int.from_bytes(code[o:o + 2], "little")
        if (w1 & 0xF800) != 0xF000:
            continue
        top = (w1 >> 4) & 0x1F
        if top not in (0x04, 0x0C):  # movw / movt
            continue
        w2 = int.from_bytes(code[o + 2:o + 4], "little")
        imm16 = ((w1 & 0xF) << 12) | (((w1 >> 10) & 1) << 11) \
                | (((w2 >> 12) & 0x7) << 8) | (w2 & 0xFF)
        if imm16 == val:
            kind = "movw" if top == 0x04 else "movt"
            out.append((o + FLASH_BASE, kind))
    return out


for path, label in (("data/servo_fw_samples/elf/v328d8.bin", "D8"),
                    ("data/servo_fw_samples/elf/v3150.bin", "3150")):
    _r, _h, code = load_image(path)
    print("=" * 70)
    print("BUILD %s" % label)
    print("=" * 70)

    print("--- POSITIVE CONTROLS (must be non-empty) ---")
    for v in CONTROLS:
        s = imm16_sites(code, v)
        print("   #0x%-6x : %3d site(s) %s" % (v, len(s), [hex(a) for a, _ in s[:4]]))

    print("--- CiA402 indices ---")
    for v in TARGETS:
        s = imm16_sites(code, v)
        tag = " ".join("%s@%x" % (k, a) for a, k in s[:6])
        print("   #0x%-6x : %3d site(s) %s" % (v, len(s), tag))
    print()
