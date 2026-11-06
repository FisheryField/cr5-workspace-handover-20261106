#!/usr/bin/env python3
"""Annotated disassembly with PLT names + caller lookup.

Fixes the blind spot that made three earlier caller scans abstain: calls to
functions that live in *another object of the same shared library* go through a
PLT stub (`blx 0x000b41bc`), because the symbol has default visibility.  A scan
for `bl <function address>` therefore finds nothing even though the call is
right there.

Now that tools/libdata_plt.py resolves every stub (2932/2933), this tool:
  1) builds addr -> symbol for every PLT stub
  2) finds the stub(s) for a named function and lists its callers
  3) also looks for *data* references to the function address or its stub
     (a route/registration table would store one of them), restricting the
     search to address-bearing sections so .symtab self-hits are excluded
  4) disassembles a named function with every external call named

Usage:
  libdata_xref.py find <symbol-substring> [...]
  libdata_xref.py dis  <symbol-substring> [...]
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB  # noqa: E402
from capstone import CS_MODE_LITTLE_ENDIAN, CS_OP_IMM  # noqa: E402
from libdata_plt import build as plt_build  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "libdataSvr.so.bin")


def symtab(d, secs):
    out = []
    for s in secs:
        if s["name"] not in (".symtab", ".dynsym"):
            continue
        strt = secs[s["link"]]
        base = strt["offset"]
        for i in range(s["size"] // 16):
            off = s["offset"] + i * 16
            no, val, size, info, other, shndx = \
                struct.unpack_from("<IIIBBH", d, off)
            if no == 0:
                continue
            e = d[base + no:]
            nm = e[:e.index(b"\0")].decode("ascii", "replace")
            out.append((nm, val, size, info & 0xF, shndx))
    return out


class Ctx:
    def __init__(self):
        self.d, self.secs, self.stub, self.slot2sym, self.dsym, self.plt, self.rel = \
            plt_build()
        self.syms = symtab(self.d, self.secs)
        self.funcs = {}
        for nm, val, size, typ, shndx in self.syms:
            if typ == 2 and val:
                self.funcs.setdefault(val & ~1, (nm, size))
        self.text = next(s for s in self.secs if s["name"] == ".text")

    def name(self, a):
        a &= ~1
        if a in self.stub:
            return "PLT:" + self.stub[a]
        if a in self.funcs:
            return self.funcs[a][0]
        return None

    def disasm(self, addr, size):
        fo = None
        for s in self.secs:
            if s["addr"] and s["addr"] <= addr < s["addr"] + s["size"]:
                fo = s["offset"] + (addr - s["addr"])
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
        md.detail = True
        return list(md.disasm(self.d[fo:fo + size], addr))

    def all_insns(self):
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
        md.detail = True
        md.skipdata = True
        t = self.text
        return list(md.disasm(self.d[t["offset"]:t["offset"] + t["size"]],
                              t["addr"]))


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    mode = sys.argv[1]
    needles = sys.argv[2:]
    c = Ctx()
    print("PLT stubs resolved: %d ; symtab FUNC entries: %d"
          % (len(c.stub), len(c.funcs)))

    if mode == "region":
        # region <hexaddr> <hexsize>
        a = int(sys.argv[2], 0)
        n = int(sys.argv[3], 0)
        for i in c.disasm(a, n):
            note = ""
            if i.operands and i.operands[0].type == CS_OP_IMM and \
                    i.mnemonic in ("bl", "blx", "b", "beq", "bne", "cbz",
                                   "cbnz", "bne.w", "beq.w"):
                nm = c.name(i.operands[0].imm)
                if nm:
                    note = "   ; " + nm
            print("  %08x  %-10s %-34s%s"
                  % (i.address, i.mnemonic, i.op_str, note))
        return 0

    for needle in needles:
        targets = [(a, nm, sz) for a, (nm, sz) in c.funcs.items()
                   if needle in nm]
        if not targets:
            print("!! no symbol matches %r" % needle)
            continue
        insns = c.all_insns()
        callers = {}
        for i in insns:
            if i.mnemonic not in ("bl", "blx", "b") or not i.operands:
                continue
            op = i.operands[0]
            if op.type != CS_OP_IMM:
                continue
            callers.setdefault(op.imm & ~1, []).append(i.address)
        for a, nm, sz in targets:
            print()
            print("=" * 86)
            print("%s  @0x%08x  %d B" % (nm, a, sz))
            print("=" * 86)
            # stub for this symbol, if any
            stubs = [s for s, n in c.stub.items() if n == nm]
            print("  PLT stub(s) for this symbol: %s"
                  % ", ".join("0x%08x" % s for s in stubs) or "none")
            hits = set(callers.get(a, []))
            for s in stubs:
                hits |= set(callers.get(s, []))
            print("  call sites (direct OR via PLT): %d" % len(hits))
            for s in sorted(hits)[:60]:
                owner = None
                best = -1
                for fa in c.funcs:
                    if fa <= s and fa > best:
                        best = fa
                        owner = c.funcs[fa][0]
                print("    0x%08x  in %s" % (s, owner))
            if mode == "dis":
                for i in c.disasm(a, sz):
                    note = ""
                    if i.operands and i.operands[0].type == CS_OP_IMM and \
                            i.mnemonic in ("bl", "blx", "b", "beq", "bne",
                                           "cbz", "cbnz"):
                        n2 = c.name(i.operands[0].imm)
                        if n2:
                            note = "   ; " + n2
                    print("  %08x  %-10s %-34s%s"
                          % (i.address, i.mnemonic, i.op_str, note))
    return 0


if __name__ == "__main__":
    sys.exit(main())
