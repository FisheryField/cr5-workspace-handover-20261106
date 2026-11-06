#!/usr/bin/env python3
"""Find every code site that references a given string (ARM PIC idiom).

The registration code for the HTTP route map must mention the route tokens
("calibrate", "home", ...).  Those tokens live in .rodata; this tool finds the
instructions that materialise their addresses.

The idiom (established and hand-verified earlier in this investigation):
    ldr  rX, [pc, #imm]        ; rX = *pool   (pool word holds an OFFSET)
    add  rX, pc                ; rX = pc + offset
    addw rX, rX, #n            ; optional fold

Positive control: the string "isRequestCalihome true" (0x00235324) is known to
be referenced from robot_control::checkRequestLoop @0x001db3e4.  The tool must
find that site; if it does not, it aborts instead of printing an empty answer.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB  # noqa: E402
from capstone import CS_MODE_LITTLE_ENDIAN  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "libdataSvr.so.bin")


class Elf:
    def __init__(self, path=P):
        self.d = open(path, "rb").read()
        (_t, _m, _v, _e, _ph, shoff, _f, _eh, _pe, _pn, shentsize, shnum,
         shstrndx) = struct.unpack_from("<HHIIIIIHHHHHH", self.d, 16)
        self.secs = []
        for i in range(shnum):
            f = struct.unpack_from("<IIIIIIIIII", self.d, shoff + i * shentsize)
            self.secs.append(dict(name_off=f[0], type=f[1], addr=f[3],
                                  offset=f[4], size=f[5], link=f[6], flags=f[2]))
        shstr = self.secs[shstrndx]
        for s in self.secs:
            e = self.d[shstr["offset"] + s["name_off"]:]
            s["name"] = e[:e.index(b"\0")].decode("ascii", "replace")

    def fileoff(self, v):
        for s in self.secs:
            if s["addr"] and s["addr"] <= v < s["addr"] + s["size"]:
                return s["offset"] + (v - s["addr"]), s["name"]
        return None, None

    def u32(self, v):
        fo, _ = self.fileoff(v)
        if fo is None or fo + 4 > len(self.d):
            return None
        return struct.unpack_from("<I", self.d, fo)[0]

    def cstr(self, v, n=120):
        fo, _ = self.fileoff(v)
        if fo is None:
            return None
        e = self.d[fo:fo + n]
        z = e.find(b"\0")
        if z <= 0:
            return None
        t = e[:z]
        if not all(32 <= c < 127 for c in t):
            return None
        return t.decode("ascii")


def scan(e):
    """Return list of (site_addr, effective_addr) for every resolved PIC site."""
    text = next(s for s in e.secs if s["name"] == ".text")
    code = e.d[text["offset"]:text["offset"] + text["size"]]
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.detail = True
    md.skipdata = True
    out = []
    pend = {}
    prev_pic = None
    for i in md.disasm(code, text["addr"]):
        ops = i.op_str
        if i.mnemonic.startswith("ldr") and "[pc" in ops:
            try:
                imm = int(ops.split("#")[1].split("]")[0].strip(), 0)
            except Exception:
                continue
            pool = ((i.address + 4) & ~3) + imm
            v = e.u32(pool)
            dst = ops.split(",")[0].strip()
            if v is None:
                prev_pic = None
                continue
            # case (b): the pool word IS an absolute address (shared objects do
            # this too when the linker can prove the target is local)
            if e.fileoff(v)[0] is not None:
                out.append((i.address, v))
            if v < 0x1000000:                        # plausible OFFSET
                pend[dst] = v
            prev_pic = None
            continue
        if i.mnemonic.startswith("add") and "pc" in ops:
            dst = ops.split(",")[0].strip()
            if dst in pend:
                # NOTE: this toolchain computes the offset relative to
                # (insn.address + 4) WITHOUT 4-byte alignment.  Aligning makes
                # every site whose `add` sits at addr % 4 == 2 land exactly 2
                # bytes short - which is how "calibrate" stayed invisible.
                eff = (i.address + 4) + pend[dst]
                out.append((i.address, eff))
                prev_pic = eff
            else:
                prev_pic = None
            continue
        if i.mnemonic == "addw" and prev_pic is not None:
            try:
                imm = int(ops.split("#")[1].strip(), 0)
            except Exception:
                imm = None
            if imm:
                out.append((i.address, prev_pic + imm))
            prev_pic = None
            continue
        prev_pic = None
    return out


def main():
    e = Elf()
    sites = scan(e)
    print("resolved PIC string-site count: %d" % len(sites))

    # ---- CONTROL -------------------------------------------------------
    ctrl_va = 0x00235324           # "isRequestCalihome true"
    ctrl_txt = e.cstr(ctrl_va)
    hits = [(a, v) for a, v in sites if v == ctrl_va]
    print("CONTROL: references to 0x%08x %r -> %d site(s) %s"
          % (ctrl_va, ctrl_txt, len(hits),
             ", ".join("0x%x" % a for a in [h[0] for h in hits])))
    if not hits:
        print("!! CONTROL FAILED - scan cannot see a known reference; abort")
        return 2
    print("CONTROL PASS")

    print()
    print("=" * 78)
    print("references to the route tokens")
    print("=" * 78)
    want = {}
    for tok in (b"calibrate", b"home", b"settings", b"coordinateSingle",
                b"readCurrentEncoder", b"goHome", b"multiCalibration",
                b"controlMode", b"panel", b"process", b"properties", b"test",
                b"state", b"exchange", b"common", b"modifyServoParams",
                b"readServoParams", b"leftRightHand"):
        # find the token as a standalone NUL-terminated string in .rodata
        for m in _iter_cstr(e, tok):
            want.setdefault(m, tok)
    print("distinct token addresses to look for: %d" % len(want))
    by_addr = {}
    for a, v in sites:
        by_addr.setdefault(v, []).append(a)
    for va in sorted(want):
        tok = want[va]
        a = by_addr.get(va, [])
        dec = e.cstr(va)
        print("  0x%08x %-20r  %d ref(s)  %s"
              % (va, tok.decode(), len(a),
                 " ".join("0x%x@%s" % (x, _owner(e, x)) for x in a[:12])))
    return 0


def _iter_cstr(e, tok):
    ro = [s for s in e.secs if s["name"] in (".rodata", ".data.rel.ro",
                                             ".data", ".text")]
    out = []
    for s in ro:
        blob = e.d[s["offset"]:s["offset"] + s["size"]]
        start = 0
        while True:
            i = blob.find(tok, start)
            if i < 0:
                break
            # must be NUL-terminated and preceded by NUL (standalone string)
            if blob[i + len(tok):i + len(tok) + 1] == b"\0" and \
                    (i == 0 or blob[i - 1:i] == b"\0"):
                out.append(s["addr"] + i)
            start = i + 1
    return out


def _owner(e, addr):
    return ""  # placeholder; filled by caller if needed


if __name__ == "__main__":
    sys.exit(main())
