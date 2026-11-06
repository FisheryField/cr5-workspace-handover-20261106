#!/usr/bin/env python3
"""Decode the master's EtherCAT process-data images out of a codesyscontrol dump.

Discovery (2026-09-24, round 37): the PLC application's input image - i.e. the
per-slave TxPDO copy that the master parses - lives in codesyscontrol's
anonymous mapping at 0x73000000 in a contiguous run of per-slave blocks with
the exact strides the controller programed into each drive's 0x1A00:

    J1 57, J2 57, J3 57, J4 93, J5 69, J6 71

Each block is the concatenation of the mapped objects in 0x1A00 order, so a
block can be decoded with nothing but the mapping log.  This tool locates the
run automatically (no hard-coded absolute offset) by searching for the
per-axis firmware VERSION WORD that every drive exposes as 0x5000:07
(0x32D8 = 3.2.D.8, 0x3150 = 3.1.5.0) at the expected relative offsets, then
prints every mapped object per axis.

Why this matters: it lets us read exactly what the master sees, which is what
the reported joint angle is computed from - without touching the bus.

Usage:  txpdo_decode.py <dump.bin> [base_hex]
"""
import struct
import sys

# object name, offset inside block, byte width  (J1..J5 / 20-entry layout)
BASE_ENTRIES = [
    ("0x6041 statusword", 0, 2),
    ("0x6061 modes display", 2, 1),
    ("0x6064 POSITION ACTUAL", 3, 4),
    ("0x606C velocity actual", 7, 4),
    ("0x6077 torque actual", 11, 2),
    ("0x6075 rated current", 13, 4),
    ("0x6076 rated torque", 17, 4),
    ("0x603F error code", 21, 2),
    ("0x6079 dc link voltage", 23, 4),
    ("0x6078 current actual", 27, 2),
    ("0x5000:02", 29, 2),
    ("0x5000:03", 31, 2),
    ("0x5000:06", 33, 2),
    ("0x5000:07 VERSION", 35, 2),
    ("0x5000:08", 37, 2),
    ("0x5002:03", 39, 4),
    ("0x5002:04", 43, 4),
    ("0x5002:06", 47, 2),
    ("0x606B velocity demand", 49, 4),
    ("0x6062 target velocity", 53, 4),
]
# J6 has one extra 2-byte entry at the front (0x5000:01) and three 4-byte
# vendor entries (0x5001:06/:07/:10) before 0x5002:03
J6_ENTRIES = [
    ("0x6041 statusword", 0, 2),
    ("0x6061 modes display", 2, 1),
    ("0x6064 POSITION ACTUAL", 3, 4),
    ("0x606C velocity actual", 7, 4),
    ("0x6077 torque actual", 11, 2),
    ("0x6075 rated current", 13, 4),
    ("0x6076 rated torque", 17, 4),
    ("0x603F error code", 21, 2),
    ("0x6079 dc link voltage", 23, 4),
    ("0x6078 current actual", 27, 2),
    ("0x5000:01", 29, 2),
    ("0x5000:02", 31, 2),
    ("0x5000:03", 33, 2),
    ("0x5000:06", 35, 2),
    ("0x5000:07 VERSION", 37, 2),
    ("0x5000:08", 39, 2),
    ("0x5001:06", 41, 4),
    ("0x5001:07", 45, 4),
    ("0x5001:10", 49, 4),
    ("0x5002:03", 53, 4),
    ("0x5002:04", 57, 4),
    ("0x5002:06", 61, 2),
    ("0x606B velocity demand", 63, 4),
    ("0x6062 target velocity", 67, 4),
]
SIZES = [57, 57, 57, 93, 69, 71]
NAMES = ["J1", "J2", "J3", "J4", "J5", "J6"]
VERSION = {0x32D8: "3.2.D.8", 0x3150: "3.1.5.0"}


def i32(b):
    return int.from_bytes(b, "little", signed=True)


def locate(d):
    """Find the block run by requiring 4 x 0x32D8 at stride 57 then 0x32D8,
    0x3150 at stride 93/69 - a very specific signature.  Returns (j1_base, j6_base)
    or None."""
    p32 = struct.pack("<H", 0x32D8)
    p50 = struct.pack("<H", 0x3150)
    cands = []
    start = 0
    while True:
        i = d.find(p32, start)
        if i < 0:
            break
        cands.append(i)
        start = i + 1
    for a in cands:
        # a = J1_base + 35, so J1_base = a - 35 and every later block's version
        # word sits at a + (cumulative size), except J6 which has one extra
        # 2-byte entry in front of 0x5000:07 -> +2.
        j4 = a + 171
        j5 = a + 264
        j6 = a + 333 + 2
        if d[a + 57:a + 59] != p32 or d[a + 114:a + 116] != p32:
            continue
        if d[j4:j4 + 2] != p32:
            continue
        if d[j5:j5 + 2] != p32:
            continue
        if d[j6:j6 + 2] != p50:
            continue
        return a - 35, j6 - 37
    return None


def main():
    path = sys.argv[1]
    base = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x73000000
    d = open(path, "rb").read()
    loc = locate(d)
    if loc is None:
        print("!! block run not found in this dump - do NOT conclude anything")
        return 2
    j1, j6 = loc
    print("dump %d bytes, base 0x%08x" % (len(d), base))
    print("located: J1 block @ dump+0x%x ; J6 block @ dump+0x%x"
          % (j1, j6))
    starts = []
    p = j1
    for s in SIZES:
        starts.append(p)
        p += s
    if starts[5] != j6:
        print("!! stride check failed (J6 @0x%x vs %0x%x) - abort" % (j6, starts[5]))
        return 2
    print("CONTROL: strides 57/57/57/93/69/71 reproduced exactly -> PASS")
    for k, (nm, st, sz) in enumerate(zip(NAMES, starts, SIZES)):
        print()
        print("=== %s  block @ %08x (dump+0x%x, %d B) ==="
              % (nm, base + st, st, sz))
        ents = J6_ENTRIES if k == 5 else BASE_ENTRIES
        for label, off, w in ents:
            if off + w > sz:
                continue
            b = d[st + off:st + off + w]
            if w == 1:
                v = b[0]
                u = v
            else:
                v = int.from_bytes(b, "little", signed=True)
                u = int.from_bytes(b, "little", signed=False)
            extra = ""
            if "VERSION" in label:
                extra = "   <- %s" % VERSION.get(u, "??")
            print("   +%-3d %-24s %10d (u=%d)%s" % (off, label, v, u, extra))
    return 0


if __name__ == "__main__":
    sys.exit(main())
