#!/usr/bin/env python3
"""Find where a function's ADDRESS is materialised in code (PIC idiom).

Established the hard way:
  * no `bl/blx` targets these handlers      -> they are called indirectly
  * no relocation slot holds their address  -> not a data pointer either
  * so the address must be computed at runtime with the PIC idiom
        ldr  rX, [pc, #imm]      ; rX = offset relative to pc
        add  rX, pc              ; rX = pc + offset      <-- THE ADDRESS
    (optionally followed by `addw rX, rX, #n`)

This sweep walks all of .text once and reports every site where such a pair
resolves to one of the functions of interest.  Those sites are the registration
points - a route table being filled, a task loop being set up, etc.

Controls: the sweep must decode a plausible number of instructions, and at
least one of the searched addresses must be produced by SOME site (a function
whose address is never materialised could never be registered, so an all-zero
result means the sweep is broken).
"""
import os
import struct
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "libdataSvr.so.bin")

TARGETS = {
    0x000F0428: "DataSubProcess::caliHome",
    0x000F9520: "DataSubProcess::updateEncoderData",
    0x000E520C: "DataSubProcess::getEncoderValue",
    0x000FBF30: "DataSubProcess::readCurrentEncoder",
    0x000FB704: "DataSubProcess::goHome",
}
SH_FMT = "<IIIIIIIIII"
SYM_FMT = "<IIIBBH"


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
        for k in range(s["size"] // (s["entsize"] or 16)):
            off = s["offset"] + k * 16
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

    def u32(v):
        for s in secs:
            if s["addr"] and s["size"] and s["addr"] <= v < s["addr"] + s["size"]:
                fo = s["offset"] + (v - s["addr"])
                if fo + 4 <= len(d):
                    return struct.unpack_from("<I", d, fo)[0]
        return None

    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.skipdata = True          # MANDATORY - see servo_img.make_md()
    md.detail = True
    code = d[text["offset"]:text["offset"] + text["size"]]
    sites = defaultdict(list)
    pend = {}
    n = 0
    for i in md.disasm(code, text["addr"]):
        n += 1
        if i.mnemonic == ".byte":
            continue
        op = i.op_str
        if i.mnemonic.startswith("ldr") and "[pc" in op:
            try:
                imm = int(op.split("#")[1].split("]")[0].strip(), 0)
            except Exception:
                continue
            pc = ((i.address + 4) & ~3) + imm
            v = u32(pc)
            if v is not None:
                dst = op.split(",")[0].strip()
                pend[dst] = v
        elif i.mnemonic.startswith("add") and "pc" in op:
            dst = op.split(",")[0].strip()
            if dst in pend:
                eff = ((i.address + 4) & ~3) + pend[dst]
                if eff in TARGETS:
                    sites[eff].append(i.address)
                # remember for a possible following addw
                pend["__eff_" + dst] = eff
        elif i.mnemonic == "addw":
            dst = op.split(",")[0].strip()
            k = "__eff_" + dst
            if k in pend:
                try:
                    imm = int(op.split("#")[1].strip(), 0)
                except Exception:
                    continue
                eff = pend[k] + imm
                if eff in TARGETS:
                    sites[eff].append(i.address)

    print(".text sweep: %d instructions decoded" % n)
    ok = n > 100000
    print("control: sweep size plausible: %s" % ok)
    if not ok:
        print("!! abort")
        return 2

    found = 0
    for addr, label in TARGETS.items():
        h = sites[addr]
        print()
        print("=" * 84)
        print("%s @0x%08x : %d address-materialisation site(s)"
              % (label, addr, len(h)))
        print("=" * 84)
        for s in h[:10]:
            o = owner(s)
            print("   site 0x%08x   in %s @0x%08x"
                  % (s, o[1] if o else "?", o[0] if o else 0))
        if h:
            found += 1
    print()
    print("addresses materialised somewhere: %d / %d" % (found, len(TARGETS)))
    if found == 0:
        print("!! none - the sweep is broken or the idiom differs; abstain")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
