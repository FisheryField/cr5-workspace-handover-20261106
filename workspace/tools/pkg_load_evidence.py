#!/usr/bin/env python3
"""Lay out every piece of evidence about the payload load address, in one place.

Conflicting observations so far:
  (a) full-length match: payload == 3.1.5.hex at 0x08010000, 100%
  (b) Reset(0x0801019D) decodes to a clean prologue only under load=0x08010000
  (c) D8 payload at load=0x08000000 offset 0x1019C gives `ble` (plausible-ish)
  (d) both payloads begin with a vector table AND contain nop/nop (00 bf) padding

Measure the discriminator directly: the Cortex-M vector table must list the
handlers in order at 4-byte stride starting at the load address, and the 7th
entry onwards are reserved zeros.  So find the offset O where vectors[] starts by
requiring: dwords 7..10 == 0 AND dword0 is an SRAM pointer AND dwords 1..6 are odd
flash addresses.  That pins the vector-table offset inside the payload.
"""
import struct

CASES = [("D8", "data/servo_fw_samples/elf/v328d8.bin"),
         ("3150", "data/servo_fw_samples/elf/v3150.bin")]

for label, path in CASES:
    pl = open(path, "rb").read()
    print("=" * 74)
    print("%s  payload %d B" % (label, len(pl)))
    print("=" * 74)

    def sp_ok(v):
        return 0x20000000 <= v < 0x20080000

    def th_ok(v):
        return (v & 1) == 1 and 0x08000000 <= (v & ~1) < 0x08200000

    print("  在 payload 里搜向量表起点（要求 dword7..10 == 0）:")
    found = []
    for o in range(0, min(len(pl) - 48, 0x40000), 4):
        d = [struct.unpack_from("<I", pl, o + 4 * k)[0] for k in range(12)]
        if not sp_ok(d[0]):
            continue
        if not all(th_ok(d[k]) for k in range(1, 7)):
            continue
        if not all(d[k] == 0 for k in range(7, 11)):
            continue
        found.append((o, d))
    print("   命中 %d 处" % len(found))
    for o, d in found[:6]:
        print("      payload offset 0x%05x  SP=0x%08x Reset=0x%08x" % (o, d[0], d[1]))
        print("         vectors: %s" % " ".join("%08x" % v for v in d[:12]))

    print()
    print("  payload 前 0x30 字节（看 nop/nop 填充位置）:")
    for o in range(0, 0x30, 8):
        print("    +0x%02x  %s" % (o, pl[o:o + 8].hex(" ")))
    print()
