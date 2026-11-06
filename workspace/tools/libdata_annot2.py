#!/usr/bin/env python3
"""Annotated disassembly v2 - with PIC string resolution.

v1 failed to name any string because this library addresses strings with the
classic ARM PIC idiom:

    ldr  r4, [pc, #0x664]     ; r4 = OFFSET relative to pc  (not an address!)
    add  r4, pc               ; r4 = pc + offset

so the literal is an offset, not a pointer.  The effective address is
    ((addr_of_add + 4) & ~3) + offset
(Thumb `add rX, pc` uses PC = instruction address + 4, word aligned).
Sometimes an `addw rX, rX, #n` follows as well, which must also be folded in.

Verified by hand before writing this: for updateEncoderData,
    ldr r4,[pc,#0x664] -> 0x0013b8e2 ; add r4,pc @0x000f954e
    => 0x000f9550 + 0x0013b8e2 = 0x00234e32, which lies in .rodata.
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
WANT = sys.argv[1:] or ["DataSubProcess17updateEncoderDataEv"]


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
        self.syms, self.funcs = {}, []
        for s in self.secs:
            if s["type"] not in (2, 11):
                continue
            strt = self.secs[s["link"]]["offset"]
            for i in range(s["size"] // (s["entsize"] or 16)):
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

    def cstr(self, v):
        fo, sec = self.fileoff(v)
        if fo is None:
            return None
        e = self.d[fo:fo + 160]
        z = e.find(b"\0")
        if z <= 0:
            return None
        t = e[:z]
        if not all(32 <= c < 127 for c in t):
            return None
        return t.decode("ascii")

    def sym_name(self, a):
        if a in self.syms:
            return self.syms[a]
        best = None
        for ad, sz, nm in self.funcs:
            if ad <= a < ad + sz and (best is None or ad > best[0]):
                best = (ad, nm)
        return "%s+0x%x" % (best[1], a - best[0]) if best else None


def main():
    e = Elf(P)
    print("libdataSvr.so : %d functions in .symtab" % len(e.funcs))
    for needle in WANT:
        hits = [(a, sz, nm) for a, sz, nm in e.funcs if needle in nm]
        if not hits:
            print("!! nothing matches %r" % needle)
            continue
        for addr, size, nm in hits:
            fo, _ = e.fileoff(addr)
            code = e.d[fo:fo + size]
            md = Cs(CS_ARCH_ARM, CS_MODE_LITTLE_ENDIAN | CS_MODE_THUMB)
            md.detail = True
            ins = [i for i in md.disasm(code, addr) if i.mnemonic != ".byte"]
            print("=" * 86)
            print("%s  @0x%08x  %d B  %d insns" % (nm, addr, size, len(ins)))
            print("=" * 86)
            pend = {}          # reg -> literal offset from an ldr [pc]
            pend_at = {}       # reg -> address of that ldr
            for idx, i in enumerate(ins):
                note = ""
                ops = getattr(i, "operands", [])
                # branch -> symbol
                for op in ops:
                    if op.type == CS_OP_IMM and i.mnemonic in ("bl", "blx", "b",
                                                               "beq", "bne", "cbz",
                                                               "cbnz", "ble", "bgt",
                                                               "bge", "blt", "bls",
                                                               "bhi", "bcs", "bcc"):
                        t = op.imm & ~1
                        sn = e.sym_name(t)
                        if sn and i.mnemonic in ("bl", "blx"):
                            note = "   ; %s" % sn
                opstr = i.op_str
                # ldr rX,[pc,#imm] : remember the OFFSET
                if i.mnemonic.startswith("ldr") and "[pc" in opstr:
                    try:
                        imm = int(opstr.split("#")[1].split("]")[0].strip(), 0)
                    except Exception:
                        imm = None
                    if imm is not None:
                        pc = ((i.address + 4) & ~3) + imm
                        v = e.u32(pc)
                        dst = opstr.split(",")[0].strip()
                        if v is not None and v > 0x10000 and v < 0x400000:
                            pend[dst] = v          # looks like a pc-relative offset
                            pend_at[dst] = i.address
                        elif v is not None:
                            s = e.cstr(v)
                            note += '   ; = 0x%08x%s' % (v, ' "%s"' % s if s else "")
                # add rX, pc   or   add.w rX, pc
                if i.mnemonic.startswith("add") and "pc" in opstr:
                    dst = opstr.split(",")[0].strip()
                    if dst in pend:
                        eff = ((i.address + 4) & ~3) + pend[dst]
                        s = e.cstr(eff)
                        note += "   ; PIC -> 0x%08x%s" % (eff, ' "%s"' % s if s else "")
                        i._pic = eff          # type: ignore
                # fold a following addw rX, rX, #imm
                if i.mnemonic == "addw" and idx > 0 and getattr(ins[idx - 1], "_pic", None):
                    try:
                        imm = int(opstr.split("#")[1].strip(), 0)
                    except Exception:
                        imm = None
                    base = getattr(ins[idx - 1], "_pic")
                    if imm:
                        eff = base + imm
                        s = e.cstr(eff)
                        note += "   ; PIC+0x%x -> 0x%08x%s" % (
                            imm, eff, ' "%s"' % s if s else "")
                        i._pic = eff          # type: ignore
                print("  %08x  %-10s %-32s%s" % (i.address, i.mnemonic, opstr, note))
            print()


if __name__ == "__main__":
    main()
