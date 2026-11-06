#!/usr/bin/env python3
"""STRICT version of the CSV-anchor test: adjacent SEQUENCES, not single values.

The single-value version produced 7418 hits - small integers are everywhere, so
that measurement carried no information.  Here only a run of N>=3 consecutive
CSV parameters in the same encoding counts; the probability of that arising by
chance in a 330 KB image is small enough to be evidence.

Also reports, for contrast, how many hits a NEGATIVE CONTROL produces: the same
procedure applied to a shuffled/implausible value set.
"""
import os
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


def enc(v, tag):
    try:
        f = float(v)
    except ValueError:
        return None
    if tag == "f32":
        return struct.pack("<f", f)
    if tag == "u32":
        return struct.pack("<I", int(f)) if f == int(f) and 0 <= f < 2**32 else None
    d = {"u16x1": 0, "u16x10": 1, "u16x100": 2}[tag]
    n = round(f * 10 ** d)
    return struct.pack("<H", int(n)) if 0 <= n <= 0xFFFF else None


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
        print("%s  (payload %d B)" % (name, len(pl)))
        print("=" * 74)
        total = 0
        for tag in ("f32", "u16x1", "u16x10", "u16x100", "u32"):
            # build every run of 3 consecutive params that encode cleanly
            runs = []
            cur = []
            for code, val in rows:
                b = enc(val, tag)
                if b is None:
                    if len(cur) >= 3:
                        runs.append(cur)
                    cur = []
                else:
                    cur.append((code, val, b))
            if len(cur) >= 3:
                runs.append(cur)

            hits = []
            for run in runs:
                for i in range(len(run) - 2):
                    pat = run[i][2] + run[i + 1][2] + run[i + 2][2]
                    j = pl.find(pat)
                    while j >= 0:
                        hits.append((j, run[i][0], run[i + 1][0], run[i + 2][0]))
                        j = pl.find(pat, j + 1)
            print("  %-8s : %d run(s) tested, %d hit(s)%s"
                  % (tag, sum(max(0, len(r) - 2) for r in runs), len(hits),
                     "" if not hits else "   <-- LOOK"))
            for h in hits[:12]:
                print("         @0x%05x  %s / %s / %s" % h)
            total += len(hits)
        print("  TOTAL sequence hits: %d" % total)

    # negative control: values that cannot plausibly be in this firmware
    print()
    print("=" * 74)
    print("NEGATIVE CONTROL (random float triples, 2000 trials)")
    print("=" * 74)
    import random
    random.seed(20260924)
    for name, rel in IMAGES.items():
        pl = payload(os.path.join(ROOT, rel))
        hit = 0
        for _ in range(2000):
            vals = [random.uniform(1, 1000) for _ in range(3)]
            pat = b"".join(struct.pack("<f", v) for v in vals)
            if pl.find(pat) >= 0:
                hit += 1
        print("  %-5s : %d/2000 random float triples found" % (name, hit))


if __name__ == "__main__":
    main()
