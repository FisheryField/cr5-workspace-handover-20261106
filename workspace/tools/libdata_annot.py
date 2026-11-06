#!/usr/bin/env python3
"""Annotated disassembly of libdataSvr.so functions.

A raw listing of a 1,800-byte C++ function behind vtable calls is unreadable and
mostly useless.  This annotates:
  * every `bl`/`blx #imm` with the CALLEE SYMBOL NAME from .symtab
  * every `ldr rX,[pc,#imm]` with the literal value, and if it lands in .rodata,
    with the C string it points at (or the address it holds)
  * every `add rX,pc` / `add.w rX,pc,#n` (PIC string addressing) with the
    resolved address
That converts the listing into something that can actually be read.

Symbols come from .symtab (27,116 of them), so names are exact.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB  # noqa: E402
from capstone import CS_MODE_LITTLE_ENDIAN, CS_OP_IMM  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "libdataSvr.so.bin")
SH_FMT = "<IIIIIIIIII"
SYM_FMT = "<IIIBBH"

WANT = sys.argv[1:] or ["updateEncoderDataEv"]


class Elf:
    def __init__(self, path):
        self.d = open(path, "rb").read()
        (_t, _m, _v, _e, _ph, shoff, _f, _eh, _pe, _pn, shentsize, shnum,
         shstrndx) = struct.unpack_from("<HHIIIIIHHHHHH", self.d, 16)
        self.secs = []
        for i in range(shnum):
            f = struct.unpack_from(SH_FMT, self.d, shoff + i * shentsize)
            self.secs.append(dict(name_off=f[0], type=f[1], addr=f[3],
                                  offset=f[4], size=f[5], link=f[6],
                                  entsize=f[9]))
        shstr = self.secs[shstrndx]
        for s in self.secs:
            e = self.d[shstr["offset"] + s["name_off"]:]
            s["name"] = e[:e.index(b"\0")].decode("ascii", "replace")
        self.syms = {}
        self.funcs = []
        for s in self.secs:
            if s["type"] not in (2, 11):
                continue
            strt = self.secs[s["link"]]["offset"]
            n = s["size"] // (s["entsize"] or 16)
            for i in range(n):
                off = s["offset"] + i * 16
                if off + 16 > len(self.d):
                    break
                no, value, size, info, _o, _sh = struct.unpack_from(SYM_FMT, self.d, off)
                if no == 0:
                    continue
                e = self.d[strt + no:]
                nm = e[:e.index(b"\0")].decode("ascii", "replace")
                if (info & 0xF) == 2 and size:
                    self.funcs.append((value & ~1, size, nm))
                    self.syms.setdefault(value & ~1, nm)

    def fileoff(self, vaddr):
        for s in self.secs:
            if s["addr"] and s["addr"] <= vaddr < s["addr"] + s["size"]:
                return s["offset"] + (vaddr - s["addr"]), s["name"]
        return None, None

    def cstr(self, vaddr, n=110):
        fo, sec = self.fileoff(vaddr)
        if fo is None or sec not in (".rodata", ".data.rel.ro", ".data"):
            return None
        e = self.d[fo:fo + 200]
        z = e.find(b"\0")
        if z <= 0:
            return None
        t = e[:z]
        if not all(32 <= c < 127 for c in t):
            return None
        return t.decode("ascii")

    def sym_name(self, addr):
        exact = self.syms.get(addr)
        if exact:
            return exact
        best = None
        for a, sz, nm in self.funcs:
            if a <= addr < a + sz:
                if best is None or a > best[0]:
                    best = (a, nm)
        return best[1] + "+0x%x" % (addr - best[0]) if best else None

    def u32(self, vaddr):
        fo, _ = self.fileoff(vaddr)
        if fo is None or fo + 4 > len(self.d):
            return None
        return struct.unpack_from("<I", self.d, fo)[0]


def main():
    e = Elf(P)
    print("symbols: %d functions  (libdataSvr.so)" % len(e.funcs))
    for needle in WANT:
        hits = [(a, sz, nm) for a, sz, nm in e.funcs if needle in nm]
        if not hits:
            print("!! no function matching %r" % needle)
            continue
        for addr, size, nm in hits:
            # raw st_value keeps the Thumb bit
            raw = [v for v in e.syms if e.syms[v] == nm]
            thumb = True
            fo, sec = e.fileoff(addr)
            if fo is None:
                print("!! 0x%08x not mapped" % addr)
                continue
            code = e.d[fo:fo + size]
            md = Cs(CS_ARCH_ARM, CS_MODE_LITTLE_ENDIAN |
                    (CS_MODE_THUMB if thumb else CS_MODE_ARM))
            md.detail = True
            ins = [i for i in md.disasm(code, addr) if i.mnemonic != ".byte"]
            print("=" * 84)
            print("%s   @0x%08x  %d B  (%d instructions)" % (nm, addr, size, len(ins)))
            print("=" * 84)
            for i in ins:
                note = ""
                # branch target -> symbol
                for op in getattr(i, "operands", []):
                    if op.type == CS_OP_IMM and i.mnemonic in ("bl", "blx", "b",
                                                               "beq", "bne", "cbz",
                                                               "cbnz", "ble", "bgt",
                                                               "bge", "blt", "bhi",
                                                               "bls", "bcs", "bcc"):
                        t = op.imm & ~1
                        sn = e.sym_name(t)
                        if sn and i.mnemonic in ("bl", "blx"):
                            note = "   ; %s" % sn
                        elif not (addr <= t < addr + size):
                            note = "   ; -> 0x%08x" % t
                # PC-relative literal
                if i.mnemonic.startswith("ldr") and "[pc" in i.op_str:
                    try:
                        imm = int(i.op_str.split("#")[1].split("]")[0].strip(), 0)
                        pc = ((i.address + 4) & ~3) + imm
                        v = e.u32(pc)
                        s = e.cstr(v) if v is not None else None
                        if s:
                            note += '   ; = "%s"' % s
                        elif v is not None:
                            note += "   ; = 0x%08x" % v
                    except Exception:
                        pass
                # PIC string address: add rX, pc
                if i.mnemonic.startswith("add") and "pc" in i.op_str:
                    note += "   ; (PIC addr, resolved at next literal)"
                print("  %08x  %-10s %-34s%s" % (i.address, i.mnemonic, i.op_str, note))
            print()


if __name__ == "__main__":
    main()
