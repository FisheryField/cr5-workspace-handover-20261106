"""dis1.py - dump Thumb disassembly around given runtime addresses, and report
nearby inline symbol-name call sites (the PLC's resolve-by-name pattern).

usage: python tools\\dis1.py 0x75b5d588 0x75b5f398 0x75b09362
"""
import os, gzip, re, struct, sys, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUMP = os.path.join(BASE_DIR, "data", "appmap", "high_73000000.bin.gz")
BASE = 0x73000000
M = gzip.open(DUMP, 'rb').read()
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
md.detail = True


def name_at(a, minlen=5):
    o = a - BASE
    if o < 0 or o >= len(M):
        return None
    j = o
    end = min(o + 240, len(M))
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


def find_call_sites_named(name):
    """all BL sites directly followed by the ASCII name"""
    enc = name.encode()
    out = []
    o = 0
    while True:
        i = M.find(enc + b"\0", o)
        if i < 0:
            break
        a = BASE + i
        for back in range(4, 10, 2):          # BL is 4 bytes: name starts at a, BL at a-4
            pass
        t = bl_target(a - 4)
        if t is not None:
            out.append((a - 4, t, a))
        o = i + 1
    return out


def show(addr, before=0x40, after=0xa0):
    lo = (addr - before) & ~1
    hi = addr + after
    o = lo - BASE
    print("--- 0x%08x .. 0x%08x ---" % (lo, hi))
    for ins in md.disasm(M[o:o + (hi - lo)], lo):
        mark = " <==" if ins.address == addr else ""
        b = M[ins.address - BASE:ins.address - BASE + ins.size]
        nm = name_at(ins.address)
        tag = ""
        if nm:
            tag = "   ; name: %s" % nm[:70]
        print("0x%08x  %-32s %-7s %-24s%s%s" %
              (ins.address, b.hex(' '), ins.mnemonic, ins.op_str, tag, mark))


def main(argv):
    for a in argv:
        addr = int(a, 16)
        nm = name_at(addr)
        print("=" * 100)
        print("### 0x%08x  name=%r" % (addr, nm))
        t = bl_target(addr - 4) if addr >= 4 else None
        print("    preceding BL target (stub): %s" % ("0x%08x" % t if t else "n/a"))
        show(addr - 4)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
