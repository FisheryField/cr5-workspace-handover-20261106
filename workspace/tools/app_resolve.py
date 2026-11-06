#!/usr/bin/env python3
"""Resolve Application.app file offsets <-> runtime addresses using the
measured mapping table (data/appmap/app_map.json).

  app_resolve.py --to-runtime 0x0e9f08 [0x0fba0c ...]
  app_resolve.py --to-file    0x75b5cf9c [0x75aa3451 ...]
  app_resolve.py --check                    # validate every run against the dump
  app_resolve.py --coverage                 # how much of the file is mapped

Exit status is 0 when every requested offset resolved inside a mapped run.
"""
import sys, json, os, gzip, hashlib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(BASE_DIR, "data", "Application.app")
TBL = os.path.join(BASE_DIR, "data", "appmap", "app_map.json")
DUMP = os.path.join(BASE_DIR, "data", "appmap", "high_73000000.bin.gz")
DUMP_BASE = 0x73000000


def load():
    t = json.load(open(TBL))
    segs = sorted(t["segments"], key=lambda s: s["file_start"])
    return t, segs


def to_runtime(segs, off):
    """runtime address of a file offset, or None if the offset is not mapped"""
    for s in segs:
        if s["file_start"] <= off < s["file_end"]:
            return s["runtime_start"] + (off - s["file_start"])
    return None


def to_file(segs, addr):
    """file offset of a runtime address, or None"""
    for s in segs:
        r_end = s["runtime_start"] + (s["file_end"] - s["file_start"])
        if s["runtime_start"] <= addr < r_end:
            return s["file_start"] + (addr - s["runtime_start"])
    return None


def neighbours(segs, off):
    """the mapped run closest before/after a file offset (gap reporting)"""
    prev = nxt = None
    for s in segs:
        if s["file_end"] <= off:
            prev = s
        if s["file_start"] > off and nxt is None:
            nxt = s
    return prev, nxt


def nearest(segs, off):
    """nearest mapped runs around an unmapped file offset"""
    prev = nxt = None
    for s in segs:
        if s["file_end"] <= off:
            prev = s
        if s["file_start"] > off and nxt is None:
            nxt = s
    return prev, nxt


def main(argv):
    t, segs = load()
    print("table: %s" % TBL)
    print("  app md5 %s  size %d (%d runs)" % (t["app_md5"], t["app_size"], len(segs)))
    if not argv:
        argv = ["--coverage"]

    if argv[0] == "--coverage":
        cov = bytearray(t["app_size"])
        for s in segs:
            for i in range(s["file_start"], s["file_end"]):
                cov[i] = 1
        print("  mapped bytes: %d / %d (%.2f%%)" %
              (sum(cov), t["app_size"], 100.0 * sum(cov) / t["app_size"]))
        # biggest unmapped holes
        holes, cur = [], None
        for i in range(t["app_size"]):
            if not cov[i]:
                if cur is None:
                    cur = [i, i]
                else:
                    cur[1] = i
            elif cur is not None:
                holes.append(tuple(cur))
                cur = None
        if cur:
            holes.append(tuple(cur))
        holes.sort(key=lambda h: h[0] - h[1])
        print("  largest unmapped holes:")
        for a, b in holes[:10]:
            print("    0x%08x..0x%08x (%d bytes)" % (a, b, b - a + 1))
        return 0

    if argv[0] == "--check":
        m = gzip.open(DUMP, 'rb').read()
        bad = 0
        for s in segs:
            a, b = s["file_start"], s["file_end"]
            do = s["runtime_start"] - DUMP_BASE
            n = b - a
            if f_bytes := open(APP, 'rb').read()[a:b]:
                pass
            if do < 0 or do + n > len(m):
                print("  OUT OF DUMP 0x%08x..0x%08x" % (a, b))
                bad += 1
                continue
            same = sum(1 for x, y in zip(open(APP, 'rb').read()[a:b], m[do:do + n]) if x == y)
            if same < 0.85 * n:
                print("  FAIL file 0x%08x..0x%08x  only %d/%d bytes agree" % (a, b, same, n))
                bad += 1
        print("  %d / %d runs failed re-check" % (bad, len(segs)))
        return 1 if bad else 0

    mode = argv[0]
    rc = 0
    for a in argv[1:]:
        v = int(a, 16) if a.lower().startswith("0x") else int(a)
        if mode == "--to-runtime":
            r = to_runtime(segs, v)
            if r is None:
                p, n = nearest(segs, v)
                print("0x%08x -> UNMAPPED" % v)
                if p:
                    print("     previous run ends at file 0x%08x (runtime 0x%08x)" %
                          (p["file_end"], p["runtime_start"] + (p["file_end"] - p["file_start"])))
                if n:
                    print("     next run starts at file 0x%08x (runtime 0x%08x)" %
                          (n["file_start"], n["runtime_start"]))
                rc = 1
            else:
                print("file 0x%08x -> runtime 0x%08x" % (v, r))
        elif mode == "--to-file":
            r = to_file(segs, v)
            if r is None:
                print("0x%08x -> UNMAPPED" % v)
                rc = 1
            else:
                print("runtime 0x%08x -> file 0x%08x" % (v, r))
        else:
            print(__doc__)
            return 2
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
