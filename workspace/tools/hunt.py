"""hunt.py - scan the Application runtime image for instruction patterns that
point at interesting structures (mailbox polling, name resolution, SDO calls).

Prints compact evidence so results can be pasted into the docs.
"""
import os, gzip, re, struct, collections, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUMP = os.path.join(BASE_DIR, "data", "appmap", "high_73000000.bin.gz")
BASE = 0x73000000
M = gzip.open(DUMP, 'rb').read()
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
md.detail = True


def is_name(o, minlen=6):
    j = o
    end = min(o + 200, len(M))
    while j < end and 0x20 <= M[j] < 0x7f:
        j += 1
    if j - o < minlen or j >= len(M) or M[j] != 0:
        return None
    return M[o:j].decode('ascii', 'replace')


def bl_target(addr):
    o = addr - BASE
    if o < 0 or o + 4 > len(M):
        return None
    hw1, hw2 = struct.unpack_from("<HH", M, o)
    if (hw1 & 0xf800) != 0xf000 or (hw2 & 0xd000) != 0xd000:
        return None
    s = (hw1 >> 10) & 1
    imm10 = hw1 & 0x3ff
    j1 = (hw2 >> 13) & 1
    j2 = (hw2 >> 11) & 1
    i1 = (~(j1 ^ s)) & 1
    i2 = (~(j2 ^ s)) & 1
    imm = (s << 24) | (i1 << 23) | (i2 << 22) | (imm10 << 12) | ((hw2 & 0x7ff) << 1)
    if imm & (1 << 24):
        imm -= (1 << 25)
    return (addr + 4 + imm) & 0xffffffff


def main():
    img_lo, img_hi = 0x75a76000, 0x75cb8000
    calls = []
    for a in range(img_lo, img_hi - 8, 2):
        t = bl_target(a)
        if t is None:
            continue
        nm = is_name(a + 4 - BASE)
        if nm:
            calls.append((a, t, nm))
    print("inline-name call sites: %d" % len(calls))
    stubs = collections.Counter(c[1] for c in calls)
    print("top stubs:")
    for t, n in stubs.most_common(10):
        print("   0x%08x  x%d" % (t, n))
    by = collections.defaultdict(list)
    for a, t, nm in calls:
        by[nm].append((a, t))
    print("\ndistinct names: %d" % len(by))
    key = [n for n in by if re.search(r'(config|Servo|servo|Axis|axis|SDO|sdo|IoConfig|Drive|drive)', n)]
    print("interesting names (%d):" % len(key))
    for n in sorted(key):
        sites = by[n]
        print("   %-60s x%d  %s" % (n[:58], len(sites),
                                    " ".join("0x%08x" % s[0] for s in sites[:5])))
    out = os.path.join(BASE_DIR, "data", "appmap", "name_calls.txt")
    with open(out, 'w') as f:
        for a, t, nm in sorted(calls):
            f.write("0x%08x\tstub=0x%08x\t%s\n" % (a, t, nm))
    print("\nwrote %s" % out)


if __name__ == "__main__":
    main()
