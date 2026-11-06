#!/usr/bin/env python3
"""Exhaustive enumeration of `bl <target>` sites with the value left in r0.

Method: every Thumb-2 BL/BLX-shaped 32-bit word in .text is verified with
capstone; then r0's value at the call is recovered by walking the decoded
instruction stream backwards from a seed that decodes straight into the site.

POSITIVE CONTROLS (assert):
  * 0x0009775e must be reported with r0 = 0x74 (hand-read earlier)
  * 0x00099c6e must be reported with r0 = 0x86 (hand-read earlier)
"""
import bisect
import re
import struct
import sys

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
from capstone.arm import ARM_OP_IMM, ARM_OP_REG

P = r"D:\mydata\workspace\data\libalgs_framework.so.bin"
DATA = open(P, "rb").read()
SH_FMT = "<IIIIIIIIII"
SYM_FMT = "<IIIBBH"
TEXT_VA, TEXT_OFF, TEXT_SZ = 0x4C340, 0x4C340, 0x15F6BA
MD = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
MD.detail = True


def load_syms():
    (_t, _m, _v, _e, _ph, e_shoff, _fl, _eh, _phes, _phn, e_shentsize,
     e_shnum, e_shstrndx) = struct.unpack_from("<HHIIIIIHHHHHH", DATA, 16)
    secs = []
    for i in range(e_shnum):
        f = struct.unpack_from(SH_FMT, DATA, e_shoff + i * e_shentsize)
        secs.append(dict(name_off=f[0], type=f[1], addr=f[3], offset=f[4],
                         size=f[5], link=f[6], entsize=f[9]))
    shstr = secs[e_shstrndx]

    def nm(o):
        s = DATA[shstr["offset"] + o:]
        return s[:s.index(b"\0")].decode("ascii", "replace")
    for s in secs:
        s["name"] = nm(s["name_off"])
    out = []
    for s in secs:
        if s["type"] not in (2, 11):
            continue
        strt = secs[s["link"]]
        base = strt["offset"]
        n = s["size"] // 16 if s["entsize"] == 0 else s["size"] // s["entsize"]
        for i in range(n):
            off = s["offset"] + i * 16
            name_o, value, size, info, _o, shndx = struct.unpack_from(SYM_FMT, DATA, off)
            if name_o == 0:
                continue
            e = DATA[base + name_o:]
            name = e[:e.index(b"\0")].decode("ascii", "replace")
            out.append((value & ~1, size, name, info & 0xF, shndx))
    return out


SY = load_syms()
ext = {}
for v, sz, nm, ty, sh in SY:
    if sh != 11 or ty != 2:
        continue
    if v not in ext or sz > ext[v][1]:
        ext[v] = (nm, sz)
FUNCS = sorted((v, sz, nm) for v, (nm, sz) in ext.items())
FS = [f[0] for f in FUNCS]


def enclosing(a):
    i = bisect.bisect_right(FS, a) - 1
    if i >= 0:
        return FUNCS[i]
    return (None, None, None)


def bl_sites(target):
    out = []
    o = TEXT_OFF
    while o <= TEXT_OFF + TEXT_SZ - 4:
        w1, w2 = struct.unpack_from("<HH", DATA, o)
        if (w1 & 0xF800) in (0xF000, 0xF800) and (w2 & 0xD000) == 0xD000:
            a = TEXT_VA + (o - TEXT_OFF)
            insns = list(MD.disasm(DATA[a:a + 4], a))
            if insns and insns[0].mnemonic in ("bl", "blx") and insns[0].operands \
                    and insns[0].operands[0].type == ARM_OP_IMM \
                    and (insns[0].operands[0].imm & ~1) == (target & ~1):
                out.append(a)
        o += 2
    return out


def r0_at(a, back=0x80):
    """Recover r0 by decoding a window that ends at `a`."""
    best = None
    for extra in range(4, 0x40, 2):
        s = a - back
        insns = list(MD.disasm(DATA[s:a + 4], s))
        idx = [k for k, i in enumerate(insns) if i.address == a]
        if not idx:
            continue
        k = idx[0]
        val = None
        how = ""
        for i in insns[max(0, k - 12):k]:
            m = i.mnemonic
            o = i.op_str
            if m in ("movs", "mov", "mov.w", "movs.w") and \
                    re.match(r"^r0, #", o):
                val = int(o.split("#")[1], 0)
                how = "%08x %s %s" % (i.address, m, o)
            elif m.startswith("add") and o.startswith("r0, "):
                mm = re.match(r"^r0, (\w+), #(\S+)$", o)
                if mm:
                    val = "%s + %s" % (mm.group(1), mm.group(2))
                    how = "%08x %s %s" % (i.address, m, o)
            elif o.startswith("r0,") and m in ("ldr", "ldrb", "ldrh", "ldr.w"):
                val = "<mem>"
                how = "%08x %s %s" % (i.address, m, o)
        best = (val, how)
        break
    return best or (None, "")


def main():
    target = int(sys.argv[1], 16)
    sites = bl_sites(target)
    print("verified bl -> 0x%08x : %d sites" % (target, len(sites)))
    reps = {}
    for a in sites:
        val, how = r0_at(a)
        reps[a] = (val, how)
    # positive controls
    for ctl_a, ctl_v in ((0x9775E, 0x74), (0x99C70, 0x86), (0x980A4, 0x72)):
        v = reps.get(ctl_a, (None, ""))[0]
        print("POSITIVE CONTROL site 0x%08x r0=%s expect %s : %s"
              % (ctl_a, v, hex(ctl_v), "PASS" if v == ctl_v else "FAIL"))
        assert v == ctl_v, "control failed at 0x%x" % ctl_a
    print()
    for a in sorted(sites):
        val, how = reps[a]
        st, sz, nm = enclosing(a)
        print("  0x%08x  r0=%-12s [%s]  %s"
              % (a, val if val is not None else "?", how, nm))
    return 0


if __name__ == "__main__":
    sys.exit(main())
