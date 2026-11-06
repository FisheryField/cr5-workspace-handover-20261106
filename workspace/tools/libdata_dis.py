#!/usr/bin/env python3
"""Disassemble named functions out of libdataSvr.so.

The library is fully symbolised (27,116 symbols) but has no usable DWARF, so
function boundaries and names come from .symtab - that is the whole advantage,
and it is enough: `caliHome`, `updateEncoderData`, `getEncoderValue` and
`readCurrentEncoder` each have an exact address and size, so nothing has to be
guessed.

ARM vs Thumb is decided per symbol by the low bit of st_value (the standard ARM
EABI convention for STT_FUNC), and a positive control then checks that the
decoded body looks like a real function (no long run of undecodable words, and
it ends in a return/branch).  If the control fails for a listed symbol the tool
says so instead of printing garbage as if it were code.
"""
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB  # noqa: E402
from capstone import CS_MODE_LITTLE_ENDIAN, CS_OP_IMM, CS_OP_MEM  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "libdataSvr.so.bin")

SH_FMT = "<IIIIIIIIII"
SYM_FMT = "<IIIBBH"

WANT = [
    "caliHome",
    "getEncoderValueEh",
    "readCurrentEncoder",
    "updateEncoderDataEv",
]


def load():
    d = open(P, "rb").read()
    (_t, _m, _v, _e, _ph, shoff, _f, _eh, _pe, _pn, shentsize, shnum,
     shstrndx) = struct.unpack_from("<HHIIIIIHHHHHH", d, 16)
    secs = []
    for i in range(shnum):
        f = struct.unpack_from(SH_FMT, d, shoff + i * shentsize)
        secs.append(dict(name_off=f[0], type=f[1], addr=f[3], offset=f[4],
                         size=f[5], link=f[6], entsize=f[9]))
    return d, secs


def syms_for(d, secs, needle):
    out = []
    for s in secs:
        if s["type"] not in (2, 11):
            continue
        strt = secs[s["link"]]
        base = strt["offset"]
        n = s["size"] // (s["entsize"] or 16)
        for i in range(n):
            off = s["offset"] + i * 16
            if off + 16 > len(d):
                break
            no, value, size, info, _o, _sh = struct.unpack_from(SYM_FMT, d, off)
            if no == 0 or (info & 0xF) != 2 or size == 0:
                continue
            e = d[base + no:]
            nm = e[:e.index(b"\0")].decode("ascii", "replace")
            if needle in nm:
                out.append((nm, value, size))
    return out


def disasm(d, secs, addr, size, thumb):
    # map vaddr -> file offset via the section that contains it
    fo = None
    for s in secs:
        if s["addr"] and s["addr"] <= addr < s["addr"] + s["size"]:
            fo = s["offset"] + (addr - s["addr"])
            break
    if fo is None:
        return None, "no section maps vaddr 0x%08x" % addr
    code = d[fo:fo + size]
    md = Cs(CS_ARCH_ARM, CS_MODE_LITTLE_ENDIAN |
            (CS_MODE_THUMB if thumb else CS_MODE_ARM))
    md.detail = True
    return list(md.disasm(code, addr)), None


def main():
    d, secs = load()
    for needle in WANT:
        hits = syms_for(d, secs, needle)
        if not hits:
            print("!! %s : NO SYMBOL - abort" % needle)
            return 2
        for nm, raw, size in hits:
            thumb = bool(raw & 1)
            addr = raw & ~1
            body, err = disasm(d, secs, addr, size, thumb)
            print("=" * 78)
            print("%s" % nm)
            print("  vaddr 0x%08x  size %d  mode %s" % (addr, size,
                                                        "THUMB" if thumb else "ARM"))
            print("=" * 78)
            if err:
                print("  !! %s" % err)
                continue
            ins = [i for i in body if i.mnemonic not in (".byte", ".word")]
            und = len(body) - len(ins)
            print("  decoded %d instructions (%d undecodable bytes)" % (len(ins), und))
            if len(ins) < 3 or und > len(body) * 0.15:
                print("  !! positive control failed - body does not decode; "
                      "wrong mode?  skipping listing")
                for i in body[:6]:
                    print("    0x%08x  %s %s" % (i.address, i.mnemonic, i.op_str))
                print()
                continue
            last = ins[-1]
            ctrl = last.mnemonic.startswith(("bx", "pop", "b", "bl"))
            print("  ends with: %s %s   %s" % (last.mnemonic, last.op_str,
                                               "(control flow OK)" if ctrl
                                               else "(!! no return - may be truncated)"))
            for i in ins:
                note = ""
                for op in getattr(i, "operands", []):
                    if op.type == CS_OP_IMM and i.mnemonic in ("bl", "blx"):
                        note = "  -> 0x%08x" % (op.imm & ~1)
                        # name the callee if we know it
                        for s in secs:
                            if s["type"] not in (2, 11):
                                continue
                            pass
                print("    0x%08x  %-9s %s%s" % (i.address, i.mnemonic, i.op_str, note))
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
