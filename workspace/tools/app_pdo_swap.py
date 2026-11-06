#!/usr/bin/env python3
"""Path B: repoint the master's joint-position PDO entry by a size-neutral swap
inside the compiled CODESYS application.

Findings that motivate this (rounds 37-39):

  * The master's reported joint angle is read from the LAST 32-bit entry of each
    axis's transmit-PDO block (proved on J2 - a 3.2.D.8 axis - and on J6).
  * For J6 that entry is `0x6062`.  On the 3.1.5.0 drive `0x6062` carries the
    RAW encoder count while the robot is enabled, whereas `0x6064` carries the
    re-based value in BOTH enable states on BOTH firmwares.
  * The per-slave transmit-PDO tables are embedded in the compiled app as plain
    records, 10 bytes each:   u16 0 | u32 (subindex<<16 | index) | u32 bit length
    Six tables in slave order J1..J6 with entry counts 20/20/20/29/23/24, which
    reproduce the measured block sizes 57/57/57/93/69/71 exactly.
  * J6's (6th) table ends with `0x6062`; entry index 2 is `0x6064`.

So: swap those two objects in J6's table only.  Both are 32-bit, so the table
length - and therefore every later offset in the process image - is unchanged.

`Application.crc` is a CODESYS wrapper holding CRC32(Application.app) in LE at
offset 4 (verified against the file), so it can be recomputed after the edit.

SAFETY: dry-run by default; every step is asserted and the tool refuses to write
unless all checks pass.
"""
import argparse
import hashlib
import struct
import sys
import zlib

REC = 10                       # u16 pad, u32 index-word, u32 bit length
NAME_TS = b"transmit pdo1"
COUNT_EXPECT = [20, 20, 20, 29, 23, 24]
# the mapping the master wrote to slave 1003 (J1) at boot, from the codesys log
J1_EXPECT = [0x6041, 0x6061, 0x6064, 0x606C, 0x6077, 0x6075, 0x6076, 0x603F,
             0x6079, 0x6078, 0x5000, 0x5000, 0x5000, 0x5000, 0x5000,
             0x5002, 0x5002, 0x5002, 0x606B, 0x6062]
SWAP_TABLE = 5                 # 6th table = slave 8 = J6


def find_tables(d):
    out = []
    s = 0
    while True:
        i = d.find(NAME_TS, s)
        if i < 0:
            break
        cnt = struct.unpack_from("<H", d, i - 12)[0]
        q = None
        for skip in range(0, 300):
            p = i + len(NAME_TS) + skip
            if p + 8 > len(d):
                break
            word, bits = struct.unpack_from("<II", d, p)
            if word == 0x6041 and bits == 16:
                q = p
                break
        out.append((i, cnt, q))
        s = i + 1
    return out


def parse(d, q, n):
    """-> list of (index, subindex, bits)"""
    res = []
    for k in range(n):
        word, bits = struct.unpack_from("<II", d, q + k * REC)
        res.append((word & 0xFFFF, word >> 16, bits))
    return res


def crc_blob(app_bytes):
    return (bytes.fromhex("b11a9000")
            + struct.pack("<I", zlib.crc32(app_bytes) & 0xFFFFFFFF)
            + b"Application\x00" + bytes.fromhex("b21a8400")
            + struct.pack("<I", 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("app")
    ap.add_argument("--out")
    ap.add_argument("--crc-out")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    orig = open(a.app, "rb").read()
    d = bytearray(orig)
    print("app: %s  %d bytes  md5=%s"
          % (a.app.split("\\")[-1], len(d), hashlib.md5(orig).hexdigest()))

    tabs = find_tables(d)
    print("transmit-PDO tables found: %d   entry counts: %s"
          % (len(tabs), [t[1] for t in tabs]))
    assert [t[1] for t in tabs] == COUNT_EXPECT, "unexpected entry counts"
    assert all(t[2] is not None for t in tabs), "could not locate an entry block"

    # CONTROL 1: table 0 must reproduce the mapping the master wrote to slave 1003
    e0 = parse(d, tabs[0][2], tabs[0][1])
    assert [x[0] for x in e0] == J1_EXPECT, \
        "table 0 does not match the master's boot-time 1A00 write for slave 1003"
    print("CONTROL 1 PASS: table 0 == the 20 entries the master wrote to slave 1003")

    # CONTROL 2: table sizes must reproduce the measured TxPDO block bytes
    sizes = [sum(b // 8 for _, _, b in parse(d, q, c)) for _, c, q in tabs]
    print("table byte sizes: %s" % sizes)
    assert sizes == [57, 57, 57, 93, 69, 71], "sizes do not match the wire blocks"
    print("CONTROL 2 PASS: sizes 57/57/57/93/69/71 match the measured wire blocks")

    ti, tc, tq = tabs[SWAP_TABLE]
    ents = parse(d, tq, tc)
    print()
    print("J6 table @0x%x : %d entries" % (ti, tc))
    for k, (ix, sub, bits) in enumerate(ents):
        print("   [%2d] %04X:%02X %2d bit%s"
              % (k, ix, sub, bits, "   <== LAST" if k == tc - 1 else ""))

    p64 = [k for k, (ix, _, _) in enumerate(ents) if ix == 0x6064]
    p62 = [k for k, (ix, _, _) in enumerate(ents) if ix == 0x6062]
    print()
    print("records with 0x6064: %s   with 0x6062: %s" % (p64, p62))
    assert len(p64) == 1 and len(p62) == 1, "expected exactly one of each"
    k64, k62 = p64[0], p62[0]
    assert k62 == tc - 1, "0x6062 is not the last entry"
    assert ents[k64][2] == 32 and ents[k62][2] == 32, "both must be 32-bit"
    print("CONTROL 3 PASS: 0x6064 at index %d, 0x6062 at index %d (LAST), both 32 bit"
          % (k64, k62))

    o64 = tq + k64 * REC
    o62 = tq + k62 * REC
    # `tq` points at the first index word, and records are REC bytes long, so
    # o64/o62 ARE the offsets of the 4-byte index words (a 2-byte pad precedes
    # each record - do NOT add 2 here).
    assert bytes(d[o64:o64 + 4]) == struct.pack("<I", 0x6064), \
        "offset of the 0x6064 index word is wrong"
    assert bytes(d[o62:o62 + 4]) == struct.pack("<I", 0x6062), \
        "offset of the 0x6062 index word is wrong"
    print()
    print("index-word offsets: 0x6064 @0x%x, 0x6062 @0x%x  (verified by bytes)"
          % (o64, o62))
    # uniqueness must be checked across the SIX TABLES (the raw byte pattern
    # legitimately repeats: every table has 0x6064 at index 2 AND every table
    # ends with 0x6062 - that is exactly why the master reads 0x6062 as the
    # joint position on all six axes).  The discriminator is the entry count:
    # only slave 8's table has 24 entries.
    n24 = [k for k, (_, c, _) in enumerate(tabs) if c == 24]
    assert n24 == [SWAP_TABLE], "24-entry tables: %s" % n24
    assert all(parse(d, q, c)[-1][0] == 0x6062 for _, c, q in tabs), \
        "not every table ends with 0x6062 - model changed, stop"
    print("UNIQUENESS PASS: tables 0..5 all end with 0x6062 (consistent with the "
          "master reading 0x6062 as position on every axis) and only table %d has "
          "24 entries, so the edit targets slave 8 alone" % SWAP_TABLE)

    # ---- swap the index words (4 bytes each) ----
    struct.pack_into("<I", d, o64, 0x6062)
    struct.pack_into("<I", d, o62, 0x6064)

    diff = [k for k in range(len(d)) if d[k] != orig[k]]
    print()
    print("bytes changed: %d -> %s"
          % (len(diff), ", ".join("0x%x" % x for x in diff)))
    # 0x6064 and 0x6062 differ only in the low byte, so the swap touches exactly
    # two bytes: 0x64->0x62 at the 0x6064 record and 0x62->0x64 at the last one.
    assert diff == [o64, o62], "unexpected change set %s" % diff
    assert orig[o64] == 0x64 and d[o64] == 0x62
    assert orig[o62] == 0x62 and d[o62] == 0x64
    print("  0x%x: 0x64 -> 0x62   (entry 2 index word  : 0x6064 -> 0x6062)" % o64)
    print("  0x%x: 0x62 -> 0x64   (entry 23 index word : 0x6062 -> 0x6064)" % o62)
    assert len(d) == len(orig), "file size changed"

    e2 = parse(d, tq, tc)
    assert e2[k64][0] == 0x6062 and e2[k64][2] == 32
    assert e2[k62][0] == 0x6064 and e2[k62][2] == 32
    assert e2[-1][0] == 0x6064, "last entry is not 0x6064"
    for k, (_, c, q) in enumerate(tabs):
        if k != SWAP_TABLE:
            assert parse(d, q, c) == parse(orig, q, c), "table %d changed!" % k
    sizes2 = [sum(b // 8 for _, _, b in parse(d, q, c)) for _, c, q in tabs]
    assert sizes2 == sizes, "sizes changed"
    print("GATE PASS: J6 table now ENDS with 0x6064 (32 bit); other five tables and "
          "all table sizes unchanged")

    blob = crc_blob(bytes(d))
    print("new .crc = %s" % blob.hex())

    if not a.write:
        print()
        print("DRY RUN - nothing written (pass --write)")
        return 0
    assert a.out, "--out required with --write"
    open(a.out, "wb").write(bytes(d))
    print("wrote %s (md5=%s)" % (a.out, hashlib.md5(bytes(d)).hexdigest()))
    if a.crc_out:
        open(a.crc_out, "wb").write(blob)
        print("wrote %s" % a.crc_out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
