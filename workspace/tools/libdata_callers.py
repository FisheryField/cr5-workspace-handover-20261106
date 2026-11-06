#!/usr/bin/env python3
"""Find the callers of a function address inside libdataSvr.so.

updateEncoderData turned out to be pure JSON bookkeeping (it reads
homeEncoder.json, finds the "encoder" array, compares its size against 4 and 9
and appends) - so the VALUES it records come from whatever calls it.  Finding
the caller is therefore the step that reaches the drive-read.

Method: disassemble the whole .text, collect every bl/blx with an immediate
target, and report those whose target lies inside the function of interest.

Positive control: self-calls inside the function itself must be found (a
function of 1,804 bytes has internal bl/blx), and the tool aborts if the sweep
decodes an implausibly small number of instructions.
"""
import os
import struct
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB  # noqa: E402
from capstone import CS_MODE_LITTLE_ENDIAN, CS_OP_IMM  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "libdataSvr.so.bin")
SH_FMT = "<IIIIIIIIII"
SYM_FMT = "<IIIBBH"

TARGETS = {
    0x000F9520: "DataSubProcess::updateEncoderData",
    0x001D9E90: "robot_control::updateEncoderData",
    0x000E520C: "DataSubProcess::getEncoderValue",
    0x000FBF30: "DataSubProcess::readCurrentEncoder",
    0x000F0428: "DataSubProcess::caliHome",
}


def main():
    d = open(P, "rb").read()
    (_t, _m, _v, _e, _ph, shoff, _f, _eh, _pe, _pn, shentsize, shnum,
     shstrndx) = struct.unpack_from("<HHIIIIIHHHHHH", d, 16)
    secs = []
    for i in range(shnum):
        f = struct.unpack_from(SH_FMT, d, shoff + i * shentsize)
        secs.append(dict(name_off=f[0], type=f[1], addr=f[3], offset=f[4],
                         size=f[5], link=f[6], entsize=f[9]))
    shstr = secs[shstrndx]
    for s in secs:
        e = d[shstr["offset"] + s["name_off"]:]
        s["name"] = e[:e.index(b"\0")].decode("ascii", "replace")

    funcs = []
    for s in secs:
        if s["type"] not in (2, 11):
            continue
        strt = secs[s["link"]]["offset"]
        for i in range(s["size"] // (s["entsize"] or 16)):
            off = s["offset"] + i * 16
            if off + 16 > len(d):
                break
            no, value, size, info, _o, _sh = struct.unpack_from(SYM_FMT, d, off)
            if no == 0 or (info & 0xF) != 2 or not size:
                continue
            e = d[strt + no:]
            funcs.append((value & ~1, size, e[:e.index(b"\0")].decode("ascii", "replace")))
    funcs.sort()

    def owner(a):
        best = None
        for ad, sz, nm in funcs:
            if ad > a:
                break
            if ad <= a < ad + sz:
                best = (ad, nm)
        return best

    text = next(s for s in secs if s["name"] == ".text")
    code = d[text["offset"]:text["offset"] + text["size"]]
    base = text["addr"]
    print(".text: 0x%08x..0x%08x (%d bytes)" % (base, base + len(code), len(code)))
    print("functions: %d" % len(funcs))

    # Thumb sweep: normalise by trying both, but ARM Linux .so built with
    # -mthumb will decode far more instructions in Thumb mode.
    best = None
    for mode, tag in ((CS_MODE_THUMB, "thumb"), (CS_MODE_ARM, "arm")):
        md = Cs(CS_ARCH_ARM, CS_MODE_LITTLE_ENDIAN | mode)
        md.detail = True
        # skipdata is MANDATORY: without it capstone stops silently at the
        # first undecodable bytes.  On this 1.3 MB .text that meant 1,333
        # instructions out of ~500k, and the only reason it was caught is the
        # "sweep too small" guard below (same lesson as servo_img.make_md).
        md.skipdata = True
        n = 0
        calls = defaultdict(list)
        for ins in md.disasm(code, base):
            n += 1
            if ins.mnemonic in ("bl", "blx", "b") and "[pc" not in ins.op_str:
                try:
                    ops = ins.operands
                except Exception:
                    continue
                if ops and ops[0].type == CS_OP_IMM and ins.mnemonic in ("bl", "blx"):
                    calls[ops[0].imm & ~1].append(ins.address)
        print("  mode=%-5s decoded %d instructions" % (tag, n))
        if best is None or n > best[0]:
            best = (n, tag, calls)
    n, tag, calls = best
    print("  -> using mode=%s (%d instructions)" % (tag, n))
    if n < 100000:
        print("!! sweep too small - abort")
        return 2

    print()
    print("=" * 80)
    print("CALLERS (addresses inside the target function)")
    print("=" * 80)
    for t, label in TARGETS.items():
        # calls whose target is inside [t, t+size)
        size = None
        for ad, sz, nm in funcs:
            if ad == t:
                size = sz
                break
        if size is None:
            print("  %s @0x%08x : no symbol" % (label, t))
            continue
        hits = []
        for target, sites in calls.items():
            if t <= target < t + size:
                for s in sites:
                    o = owner(s)
                    hits.append((s, o))
        print("  %s @0x%08x (size %d): %d call site(s)"
              % (label, t, size, len(hits)))
        for s, o in sorted(hits)[:40]:
            if o and o[0] != t:
                print("      call @0x%08x  in %s @0x%08x" % (s, o[1], o[0]))
            elif o:
                print("      call @0x%08x  (internal use)" % s)
        if len(hits) > 40:
            print("      ... %d more" % (len(hits) - 40))
    return 0


if __name__ == "__main__":
    sys.exit(main())
