#!/usr/bin/env python3
"""Can we ANCHOR the servo firmware's parameter area using the official CSVs?

Idea: data/official/servoCSV/{J1..J6}.csv are the per-joint parameter tables
that the vendor's tool writes into the drive.  If the firmware embeds such a
table, we can locate that region by matching the CSV's numbers, and then we
have a NAMED anchor (H-codes) inside an otherwise anonymous image.

Caveat being tested: readme says the CSVs target CR servo V4.1.3.3, and our
drives are the V3 line (3.1.5.0 / 3.2.D.8), so the values may simply not be
there.  This tool answers that with a measurement instead of an assumption.

Encodings tried per CSV value v:
    f32  = struct.pack('<f', v)
    u16s = round(v * 10**d) as u16   for d in 0,1,2,3
    u32  = int(v) as u32
"""
import os
import re
import struct
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES = {"D8": "data/servo_fw_samples/elf/v328d8.bin",
          "3150": "data/servo_fw_samples/elf/v3150.bin"}


def payload(p):
    d = open(p, "rb").read()
    if d[:4] == bytes.fromhex("d4c3b2a1"):
        d = d[0x20:]
    return d


def read_csv(path):
    t = open(path, "rb").read().decode("gbk", "replace")
    rows = []
    for ln in t.splitlines():
        f = ln.split(",")
        # NOTE: J1..J6.csv use "H0.00" (one-char group) while param.csv uses
        # "H00.00" (two-char group).  Requiring exactly two chars made this
        # return 0 rows silently - the 8th instance of that failure class in
        # this workspace, so the caller asserts a positive count.
        if len(f) >= 4 and re.fullmatch(r"H[0-9A-F]{1,2}\.[0-9]{2}", f[0].strip()):
            try:
                rows.append((f[0].strip(), f[3].strip()))
            except Exception:
                pass
    return rows


def encodings(vs):
    out = {}
    try:
        v = float(vs)
    except ValueError:
        return out
    out["f32"] = struct.pack("<f", v)
    for d, tag in ((0, "u16x1"), (1, "u16x10"), (2, "u16x100"), (3, "u16x1000")):
        n = round(v * 10 ** d)
        if 0 <= n <= 0xFFFF:
            out[tag] = struct.pack("<H", n)
    if 0 <= v <= 0xFFFFFFFF and v == int(v):
        out["u32"] = struct.pack("<I", int(v))
    return out


def main():
    rows = {j: read_csv(os.path.join(ROOT, "data/official/servoCSV/%s.csv" % j))
            for j in ("J1", "J6")}
    for j, r in rows.items():
        print("%s.csv: %d parameter rows" % (j, len(r)))
    if min(len(r) for r in rows.values()) < 50:
        print("!! PARSER RETURNED (ALMOST) NOTHING - aborting, the regex or the "
              "encoding is wrong, this is not a measurement of absence")
        return 2

    # distinctive = values that are not tiny integers (too common to be evidence)
    def distinctive(r):
        keep = []
        for k, v in r:
            try:
                f = float(v)
            except ValueError:
                continue
            if abs(f) >= 1.0 and f != int(f) or abs(f) >= 10:
                keep.append((k, v, f))
        return keep[:200]

    for j in ("J1", "J6"):
        print()
        print("=" * 74)
        print("%s : do its distinctive values exist in the firmware?" % j)
        print("=" * 74)
        for name, rel in IMAGES.items():
            pl = payload(os.path.join(ROOT, rel))
            hits = defaultdict(list)
            for k, vs, f in distinctive(rows[j]):
                for tag, pat in encodings(vs).items():
                    i = pl.find(pat)
                    n = 0
                    while i >= 0 and n < 40:
                        hits[(k, tag)].append(i)
                        i = pl.find(pat, i + 1)
                        n += 1
            tot = sum(len(v) for v in hits.values())
            print("  %-5s : %d match(es) across %d (param,encoding) pairs"
                  % (name, tot, len(hits)))
            for (k, tag), offs in sorted(hits.items()):
                print("      %-8s %-8s x%-3d  @ %s"
                      % (k, tag, len(offs),
                         " ".join("0x%05x" % o for o in offs[:6])))

    # anchor strings
    print()
    print("=" * 74)
    print("anchor strings / version numbers")
    print("=" * 74)
    for name, rel in IMAGES.items():
        pl = payload(os.path.join(ROOT, rel))
        print("  --- %s ---" % name)
        for label, pat in (("ascii '100121'", b"100121"),
                           ("ascii '16691'", b"16691"),
                           ("u16 16691 (0x4133)", struct.pack("<H", 16691)),
                           ("f32 16691.0", struct.pack("<f", 16691.0)),
                           ("ascii 'Version'", b"Version")):
            i = pl.find(pat)
            offs = []
            while i >= 0 and len(offs) < 5:
                offs.append(i)
                i = pl.find(pat, i + 1)
            print("      %-22s : %s" % (label,
                                        " ".join("0x%05x" % o for o in offs) or "(none)"))


if __name__ == "__main__":
    main()
