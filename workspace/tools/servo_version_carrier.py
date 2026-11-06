#!/usr/bin/env python3
"""Does the servo payload carry a version string / version code?

The controller's tool has a "The firmware version is the same, slave%d no need
to update %s." guard, and that guard has never actually fired in the logs we
have (every successful self-made flash was preceded by a flash of the OTHER
version).  Before flashing a patched 3.1.5.0 onto an axis that already runs
3.1.5.0, find out how a version is even expressed in this file.
"""
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES = {
    "D8  (3.2.D.8)": "data/servo_fw_samples/elf/v328d8.bin",
    "3150(3.1.5.0)": "data/servo_fw_samples/elf/v3150.bin",
}
# the slave reports its version over EtherCAT as a 16-bit word: 0x32D8 / 0x3150
VERWORD = {"D8  (3.2.D.8)": 0x32D8, "3150(3.1.5.0)": 0x3150}
PATTERNS = [rb"3\.1\.5\.0", rb"3\.2\.D\.8", rb"3\.2\.d\.8",
            rb"V3\.1", rb"V3\.2", rb"[0-9]\.[0-9]\.[0-9]\.[0-9]"]


def payload(p):
    d = open(p, "rb").read()
    if d[:4] == bytes.fromhex("d4c3b2a1"):
        d = d[0x20:]
    return d


for name, rel in IMAGES.items():
    pl = payload(os.path.join(ROOT, rel))
    print("=" * 74)
    print("%s  payload %d B (0x%x)" % (name, len(pl), len(pl)))
    print("=" * 74)

    print("  -- version-like ASCII strings --")
    any_hit = False
    for pat in PATTERNS:
        for m in re.finditer(pat, pl):
            s = pl[max(0, m.start() - 40):m.start() + 40]
            s = re.sub(rb"[^\x20-\x7e]", b".", s).decode("ascii")
            print("     @0x%05x (flash 0x%08x)  %r" % (m.start(), 0x08010000 + m.start(), s))
            any_hit = True
    if not any_hit:
        print("     (none - no version text in the payload at all)")

    vw = VERWORD[name]
    print("  -- occurrences of the 16-bit version WORD 0x%04x --" % vw)
    lo, hi = vw & 0xFF, vw >> 8
    n = 0
    for i in range(0, len(pl) - 2, 2):
        if struct.unpack_from("<H", pl, i)[0] == vw:
            print("     little-endian @0x%05x (flash 0x%08x)" % (i, 0x08010000 + i))
            n += 1
    print("     LE halfword matches: %d" % n)
    # also look for the literal-pool dword form
    n2 = 0
    for i in range(0, len(pl) - 4, 4):
        if struct.unpack_from("<I", pl, i)[0] == vw:
            print("     as dword     @0x%05x (flash 0x%08x)" % (i, 0x08010000 + i))
            n2 += 1
    print("     dword matches: %d" % n2)
    print()
