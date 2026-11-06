#!/usr/bin/env python3
"""CSV anchor, third attempt - with the degenerate-value filter that the first
two attempts lacked.

Failure history of this idea, kept because each was a different trap:
  v1  single values          -> 7418 hits, all coincidence (small ints)
  v2  sequences of 3         -> 790841 hits, because runs of 0/1 encode to
                                all-zero bytes and match every zero region
  v3  (this) every value in a run must be a NON-INTEGER with |v| >= 2 for f32,
      and >= 1000 for the integer encodings, so the byte pattern is unique-ish.
A matched negative control (same count of random non-integer values) runs too;
if the control scores similar to the real CSV, the method has no power.
"""
import os
import random
import re
import struct
import sys

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
    out = []
    for ln in t.splitlines():
        f = ln.split(",")
        if len(f) >= 4 and re.fullmatch(r"H[0-9A-F]{1,2}\.[0-9]{2}", f[0].strip()):
            out.append((f[0].strip(), f[3].strip()))
    return out


def enc_ok(v, tag):
    """(bytes, ok) where ok means 'distinctive enough to be evidence'."""
    try:
        f = float(v)
    except ValueError:
        return None, False
    if tag == "f32":
        if f == int(f) or abs(f) < 2.0:
            return None, False
        return struct.pack("<f", f), True
    if tag == "u32":
        if f != int(f) or f < 1000 or f > 2 ** 32:
            return None, False
        return struct.pack("<I", int(f)), True
    d = {"u16x1": 0, "u16x10": 1, "u16x100": 2}[tag]
    n = round(f * 10 ** d)
    if f == 0 or n < 1000 or n > 0xFFFF:
        return None, False
    return struct.pack("<H", int(n)), True


def runs_of(rows, tag):
    runs, cur = [], []
    for code, val in rows:
        b, ok = enc_ok(val, tag)
        if ok:
            cur.append((code, val, b))
        else:
            if len(cur) >= 2:
                runs.append(cur)
            cur = []
    if len(cur) >= 2:
        runs.append(cur)
    return runs


def main():
    rows = read_csv(os.path.join(ROOT, "data/official/servoCSV/J1.csv"))
    if len(rows) < 50:
        print("!! parser produced %d rows - aborting" % len(rows))
        return 2
    print("J1.csv parsed: %d rows" % len(rows))

    for name, rel in IMAGES.items():
        pl = payload(os.path.join(ROOT, rel))
        print()
        print("=" * 74)
        print("%s (payload %d B)" % (name, len(pl)))
        print("=" * 74)
        for tag in ("f32", "u16x1", "u16x10", "u16x100", "u32"):
            rr = runs_of(rows, tag)
            pats = []
            for run in rr:
                for i in range(len(run) - 1):
                    pats.append((run[i][0] + "/" + run[i + 1][0],
                                 run[i][2] + run[i + 1][2]))
            hits = []
            for label, pat in pats:
                j = pl.find(pat)
                while j >= 0:
                    hits.append((j, label))
                    j = pl.find(pat, j + 1)
            print("  %-8s : %4d distinctive pair-pattern(s) tested -> %d hit(s)"
                  % (tag, len(pats), len(hits)))
            for h in hits[:8]:
                print("        @0x%05x  %s" % h)

    # matched negative control
    print()
    print("=" * 74)
    print("NEGATIVE CONTROL (same number of random distinctive values)")
    print("=" * 74)
    random.seed(20260924)
    n_nonint = sum(1 for _, v in rows
                   if _is_float(v) and float(v) != int(float(v)))
    print("  CSV non-integer values: %d" % n_nonint)
    for name, rel in IMAGES.items():
        pl = payload(os.path.join(ROOT, rel))
        hit = 0
        for _ in range(max(n_nonint * 4, 200)):
            vals = [round(random.uniform(2, 5000), 3) for _ in range(2)]
            pat = b"".join(struct.pack("<f", v) for v in vals)
            if pl.find(pat) >= 0:
                hit += 1
        print("  %-5s : %d random non-integer float pairs found" % (name, hit))


def _is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    main()
