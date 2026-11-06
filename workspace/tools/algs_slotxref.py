#!/usr/bin/env python3
"""Cross-reference the GOT slots used by the alarm-134 check.

Scans .text for the movw/movt materialisation of a slot offset (the value
loaded by `ldr rX,[pc,#..]` right before `ldr rY,[r7,rX]`) and reports the
enclosing symbol for each site, so data producers/consumers can be found.

Positive control: the known slot 0x1774 (gSR6Params) must appear at 0x000940d6.
"""
import bisect
import re
import struct
import sys

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
from capstone.arm import ARM_OP_MEM, ARM_OP_REG

P = r"D:\mydata\workspace\data\libalgs_framework.so.bin"
DATA = open(P, "rb").read()
SH_FMT = "<IIIIIIIIII"
SYM_FMT = "<IIIBBH"
TEXT_VA, TEXT_OFF, TEXT_SZ = 0x4C340, 0x4C340, 0x15F6BA
SLOT = {"0x1774": "gSR6Params", "0x186c": "gActualVelocity",
        "0x15d4": "gRobotAxisMove", "0x1614": "robotAxesGroup",
        "0x162c": "gAlarmSysState"}


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


def find_slot_refs(slot):
    """find ldr rX,[pc,#imm] whose literal == slot, i.e. movw rX,#slot"""
    pat = struct.pack("<H", slot)
    out = []
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.detail = True
    for st, sz, nm in FUNCS:
        if sz == 0 or st < TEXT_VA or st >= TEXT_VA + TEXT_SZ:
            continue
        insns = list(md.disasm(DATA[st:st + sz], st))
        end = insns[-1].address + insns[-1].size if insns else st
        cover = range(0, len(insns))
        for k, insn in enumerate(insns):
            if insn.mnemonic not in ("ldr", "ldr.w"):
                continue
            for op in insn.operands:
                if op.type == ARM_OP_MEM and insn.reg_name(op.mem.base) == "pc":
                    pc = (insn.address + 4) & ~3
                    # full literal must live inside [st, st+sz] to be trusted,
                    # otherwise it belongs to the next function's pool
                    lit = pc + op.mem.disp
                    if not (st <= lit < st + sz):
                        break
                    v = struct.unpack_from("<I", DATA, lit)[0]
                    if v == slot:
                        out.append((insn.address, st, sz, nm))
                    break
    return out


def main():
    # POSITIVE CONTROL
    ctl = find_slot_refs(0x1774)
    hit = [c for c in ctl if c[0] == 0x940D6]
    print("POSITIVE CONTROL slot 0x1774 @0x940d6 present: %s (total sites %d)"
          % ("PASS" if hit else "FAIL", len(ctl)))
    assert hit, "control failed"

    for slot, slotname in SLOT.items():
        s = int(slot, 16)
        refs = find_slot_refs(s)
        funcs = []
        for a, st, sz, nm in refs:
            if (st, nm) not in funcs:
                funcs.append((st, nm))
        print()
        print("=" * 78)
        print("slot %s (%s): %d literal sites in %d functions"
              % (slot, slotname, len(refs), len(funcs)))
        print("=" * 78)
        for st, nm in funcs:
            print("   %s @0x%08x" % (nm, st))
    return 0


if __name__ == "__main__":
    sys.exit(main())
