#!/usr/bin/env python3
"""Who calls DataSubProcess::caliHome?  (redo of the caller scan, carefully)

Context: three earlier caller-finding methods on libdataSvr.so abstained, which
made me suspect the call is indirect.  But before believing that, this tool
re-does the *direct* branch-target scan with an explicit, self-validating
control:

  CONTROL  branch targets should overwhelmingly coincide with known FUNC symbol
           entry addresses.  If they do not, my decoder is broken and every
           "0 callers" result is worthless.

Then it reports callers of:
  * DataSubProcess::caliHome                (the zero-calibration handler)
  * DataSubProcess::updateEncoderData       (the homeEncoder.json writer)
  * DataSubProcess::readCurrentEncoder
  * DataSubProcess::getEncoderValue
  * PluginBase::alloc_GetServoEncoderValue  (the raw-encoder source)
  * PluginBase::alloc_SetHOMECmd
plus, for every target, an ARM/Thumb decode sanity check.

Also dumps the vtable-indirect idiom  ldr rX,[rY,#imm] ; blx rX  around the
wrapper body, since the wrapper itself calls vtable+0xb8.
"""
import os
import re
import struct
import sys

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "libdataSvr.so.bin")

TARGETS = {
    "DataSubProcess::caliHome": 0x000F0428,
    "DataSubProcess::updateEncoderData": 0x000F9520,
    "DataSubProcess::getEncoderValue": 0x000E520C,
    "DataSubProcess::readCurrentEncoder": 0x000FBF30,
    "DataSubProcess::goHome": 0x000FB704,
    "DataSubProcess::conn_req_dir": 0x001002C4,
    "robot_control::updateEncoderData": 0x001D9E90,
    "PluginBase::alloc_GetServoEncoderValue": 0x00162938,
    "PluginBase::alloc_GetEncoderValue": 0x00163674,
    "PluginBase::alloc_SetHOMECmd": 0x0015E894,
    "DataSubProcess::caliCoord6Axes": 0x000F0508,
    "DataSubProcess::caliCoord6AxesSingle": 0x000FAFA0,
}


def load():
    d = open(P, "rb").read()
    assert d[:4] == b"\x7fELF"
    (e_type, e_machine, _v, e_entry, e_phoff, e_shoff, _fl, _eh,
     _phentsize, _phnum, e_shentsize, e_shnum, e_shstrndx) = \
        struct.unpack_from("<HHIIIIIHHHHHH", d, 16)
    secs = []
    for i in range(e_shnum):
        f = struct.unpack_from("<IIIIIIIIII", d, e_shoff + i * e_shentsize)
        secs.append(dict(name_off=f[0], type=f[1], flags=f[2], addr=f[3],
                         offset=f[4], size=f[5], link=f[6], info=f[7],
                         align=f[8], entsize=f[9]))
    shstr = secs[e_shstrndx]

    def nm(o):
        s = d[shstr["offset"] + o:]
        return s[:s.index(b"\0")].decode("ascii", "replace")
    for s in secs:
        s["name"] = nm(s["name_off"])
    return d, secs


def symtab(d, secs):
    out = []
    for s in secs:
        if s["name"] not in (".symtab", ".dynsym"):
            continue
        strt = secs[s["link"]]
        base = strt["offset"]
        n = s["size"] // 16
        for i in range(n):
            off = s["offset"] + i * 16
            name_o, value, size, info, other, shndx = \
                struct.unpack_from("<IIIBBH", d, off)
            if name_o == 0:
                continue
            e = d[base + name_o:]
            name = e[:e.index(b"\0")].decode("ascii", "replace")
            out.append((name, value, size, info & 0xF, info >> 4, shndx))
    return out


def main():
    d, secs = load()
    syms = symtab(d, secs)
    func_addr = {}
    for name, val, size, typ, bind, shndx in syms:
        if typ == 2 and val:
            func_addr.setdefault(val & ~1, name)
    print("symbols=%d  distinct FUNC entry addrs=%d" % (len(syms), len(func_addr)))

    text = next(s for s in secs if s["name"] == ".text")
    code = d[text["offset"]:text["offset"] + text["size"]]
    base = text["addr"]
    print(".text addr=0x%08x size=0x%x" % (base, text["size"]))

    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.skipdata = True
    md.detail = True

    from collections import defaultdict
    callers = defaultdict(list)          # only real CALLS (bl/blx)
    callers_bl = defaultdict(list)
    callers_blx = defaultdict(list)
    n_insn = 0
    n_bl = 0
    n_blx = 0
    for insn in md.disasm(code, base):
        n_insn += 1
        m = insn.mnemonic
        if m in ("bl", "blx") and insn.operands and \
                insn.operands[0].type == 2:            # CS_OP_IMM
            t = insn.operands[0].imm
            callers[t].append(insn.address)
            if m == "bl":
                n_bl += 1
                callers_bl[t].append(insn.address)
            else:
                n_blx += 1
                callers_blx[t].append(insn.address)
    print("instructions=%d  calls bl=%d blx=%d" % (n_insn, n_bl, n_blx))

    # ---- CONTROL -------------------------------------------------------
    # Only real calls (bl/blx <imm>) should land on function entries.  Intra-
    # function conditional branches would legitimately not, so they are
    # excluded from the control.
    print()
    print("=" * 78)
    print("CONTROL: do CALL targets land on symbol entries?")
    print("=" * 78)
    for tag, tbl in (("bl", callers_bl), ("blx", callers_blx)):
        tgt = [t for t in tbl if base <= t < base + text["size"]]
        hit = [t for t in tgt if (t & ~1) in func_addr]
        print("  %-4s internal targets: %-7d FUNC-symbol starts: %-7d (%.1f%%)"
              % (tag, len(tgt), len(hit),
                 100.0 * len(hit) / max(1, len(tgt))))
        # sample a few misses to see what they are
        miss = [t for t in tgt if (t & ~1) not in func_addr][:6]
        for t in miss:
            print("        miss 0x%08x" % t)
    tgt = [t for t in callers if base <= t < base + text["size"]]
    hit = [t for t in tgt if (t & ~1) in func_addr]
    if len(tgt) and len(hit) / len(tgt) < 0.5:
        print("  !! CONTROL FAILED - decoder or symbol mapping is wrong; abort")
        return 2
    print("  CONTROL PASS (%d/%d = %.1f%%)"
          % (len(hit), len(tgt), 100.0 * len(hit) / max(1, len(tgt))))

    print()
    print("=" * 78)
    print("CALLERS")
    print("=" * 78)
    for label, addr in TARGETS.items():
        a = addr & ~1
        sites = sorted(set(callers.get(a, []) + callers.get(a | 1, [])))
        nm = func_addr.get(a, "<no symbol at that address>")
        print()
        print("  %s" % label)
        print("    addr 0x%08x  symbol@addr=%s" % (a, nm))
        print("    caller sites: %d" % len(sites))
        for s in sites[:40]:
            owner = None
            best = -1
            for fa, fn in func_addr.items():
                if fa <= s and fa > best:
                    # only accept as owner if the function is reasonably near
                    best = fa
                    owner = fn
            print("      0x%08x   (nearest lower FUNC start 0x%08x %s)"
                  % (s, best, owner))

    # ---- the wrapper body itself ---------------------------------------
    print()
    print("=" * 78)
    print("caliHome wrapper body (indirect call evidence)")
    print("=" * 78)
    a = TARGETS["DataSubProcess::caliHome"] & ~1
    off = a - base
    for insn in md.disasm(code[off:off + 96], a):
        print("   0x%08x  %-10s %s" % (insn.address, insn.mnemonic,
                                       insn.op_str))

    # ---- vtable-indirect idiom census ----------------------------------
    print()
    print("=" * 78)
    print("indirect-call idiom census: ldr rX,[rY,#imm] ; ... ; blx rX")
    print("=" * 78)
    insns = list(md.disasm(code, base))
    cnt = 0
    for i, insn in enumerate(insns):
        if insn.mnemonic != "blx" or not insn.operands:
            continue
        op = insn.operands[0]
        if op.type != 1:                       # must be a register
            continue
        reg = insn.reg_name(op.reg)
        # look back up to 8 instructions for ldr reg,[...]
        for j in range(i - 1, max(-1, i - 9), -1):
            p = insns[j]
            if p.mnemonic in ("ldr", "ldr.w") and p.operands and \
                    p.operands[0].type == 1 and p.reg_name(p.operands[0].reg) == reg:
                cnt += 1
                if cnt <= 25:
                    print("   0x%08x  blx %s   <- 0x%08x  %s %s"
                          % (insn.address, reg, p.address, p.mnemonic,
                             p.op_str))
                break
    print("  total such sites: %d" % cnt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
