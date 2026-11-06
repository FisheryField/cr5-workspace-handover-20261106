#!/usr/bin/env python3
"""Parse the per-slave PDO mapping tables embedded in Application.app.

Round 39 discovery: the compiled CODESYS application carries the device
description for the DS121 drives as PLAIN little-endian records:

    u32 = (index << 16) | subindex      u32 = bit length

preceded by a small header and a NUL-padded name ("receive pdo1" /
"transmit pdo1").  There are six transmit-PDO tables - one per servo slave -
and they differ, exactly as the master's boot-time 0x1A00 writes differ.

This matters because the master's reported joint angle for each axis is read
from the LAST entry of that axis's transmit-PDO table, so if we can identify
and (size-neutrally) swap two 32-bit entries here, we can change which object
the master uses - purely on the controller side.

Usage: txpdo_app_tables.py <Application.app>
"""
import struct
import sys

NAME_TS = b"transmit pdo1"
NAME_RS = b"receive pdo1"
BITS_OK = (8, 16, 32)


def parse_table(d, name_off):
    """name_off points at the literal name; returns (header_u16s, entries)."""
    # header: the 12 bytes immediately before the name
    hdr = d[name_off - 12:name_off]
    hs = struct.unpack("<6H", hdr)
    # entries start after the NUL-padded name; the name field is fixed size, so
    # scan forward byte by byte for the first plausible record (do NOT assume
    # 4-byte alignment - the pads are not always word aligned)
    p = name_off + len(NAME_TS)
    for skip in range(0, 240):
        q = p + skip
        if q + 8 > len(d):
            break
        idx, bits = struct.unpack_from("<II", d, q)
        if (idx >> 16) == 0x6041 and (idx & 0xFFFF) == 0 and bits == 16:
            return hs, q
    return hs, None


def dump(d, q, n, label):
    print("   %s : %d entries" % (label, n))
    out = []
    for k in range(n):
        idx, bits = struct.unpack_from("<II", d, q + k * 8)
        out.append((idx, bits))
    for k, (idx, bits) in enumerate(out):
        mark = "   <== LAST" if k == n - 1 else ""
        print("      [%2d] %04X:%02X  %2d bit%s"
              % (k, idx >> 16, idx & 0xFFFF, bits, mark))
    return out


def main():
    path = sys.argv[1]
    d = open(path, "rb").read()
    offs = []
    s = 0
    while True:
        i = d.find(NAME_TS, s)
        if i < 0:
            break
        offs.append(i)
        s = i + 1
    print("%s : %d bytes ; 'transmit pdo1' tables: %d"
          % (path.split("\\")[-1], len(d), len(offs)))
    if not offs:
        print("!! none found - do NOT conclude anything")
        return 2
    for n, o in enumerate(offs):
        hs, q = parse_table(d, o)
        print()
        print("=" * 70)
        print("TABLE %d @ file 0x%x   header u16s = %s"
              % (n, o, " ".join("0x%04x" % x for x in hs)))
        print("=" * 70)
        if q is None:
            print("   !! could not locate entry block")
            continue
        # header[1] looked like the entry count in the dumps; verify
        cnt = hs[1]
        if 1 <= cnt <= 40:
            dump(d, q, cnt, "entries (header count)")
        else:
            # fall back: walk until records stop looking sane
            k = 0
            while True:
                idx, bits = struct.unpack_from("<II", d, q + k * 8)
                if bits not in BITS_OK or (idx >> 16) < 0x1000:
                    break
                k += 1
                if k > 40:
                    break
            dump(d, q, k, "entries (scanned)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
