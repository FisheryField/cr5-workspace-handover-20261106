#!/usr/bin/env python3
"""Reconstruct the HTTP route table of libdataSvr.so.

Established this round:
  * /calibrate/home is served by codesyscontrol (pid 375, port 22000), which
    loads libdataSvr.so        -> gcontrol is NOT involved
  * DataSubProcess::conn_req_dir dispatches through a two-level
        QHash< QString(type), QHash< QString(uri), void(*)(evhttp_request*,void*) > >
    living at this+0x10CC
  * DataSubProcess::DataSubProcess(int,QString) - the CONSTRUCTOR - fills it

The registration idiom (GOT base r6 = 0x00269920, proven by the constructor's
own prologue: ldr r6,[pc,#0xd70] ; add r6,pc -> 0x00269920):

    ldr  r0, [pc,#a] ; add r0, pc     ; r0 = &"<uri>"  (C string in .rodata)
    mov  r1, #-1
    blx  QString::fromAscii_helper
    ... QHash<...>::operator[] ...
    ldr  r3, [pc,#b] ; ldr r3, [r6, r3]   ; r3 = *(GOT + b) = handler
    str  r3, [r0]

So (a) the pool word after the QString key load gives the uri, and (b) the GOT
slot resolves through .rel.plt to the handler's symbol name.

Positive control: the tool must resolve at least one entry whose handler name is
a DataSubProcess HTTP handler and must find >= 20 entries.  Otherwise it aborts.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB  # noqa: E402
from capstone import CS_MODE_LITTLE_ENDIAN  # noqa: E402
from libdata_plt import sections, dynsyms  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "libdataSvr.so.bin")
GOT = 0x00269920


def main():
    d = open(P, "rb").read()
    secs = sections(d)
    dsym = dynsyms(d, secs)
    text = next(s for s in secs if s["name"] == ".text")
    code = d[text["offset"]:text["offset"] + text["size"]]
    base = text["addr"]

    # GOT slot -> symbol, from every relocation section that targets the GOT
    slot2sym = {}
    for s in secs:
        if s["type"] not in (4, 9):
            continue
        for i in range(s["size"] // (12 if s["type"] == 4 else 8)):
            if s["type"] == 4:
                off, info, add = struct.unpack_from("<IIi", d,
                                                    s["offset"] + i * 12)
            else:
                off, info = struct.unpack_from("<II", d, s["offset"] + i * 8)
            if info & 0xFF not in (21, 22, 23, 17, 18):   # GLOB_DAT/JUMP_SLOT/...
                continue
            slot2sym[off] = dsym[info >> 8]
    print("GOT slots with a named relocation: %d" % len(slot2sym))

    def fileoff(v):
        for s in secs:
            if s["addr"] and s["addr"] <= v < s["addr"] + s["size"]:
                return s["offset"] + (v - s["addr"])
        return None

    def cstr(v):
        fo = fileoff(v)
        if fo is None:
            return None
        e = d[fo:fo + 96]
        z = e.find(b"\0")
        if z <= 0:
            return None
        t = e[:z]
        if not all(32 <= c < 127 for c in t):
            return None
        return t.decode("ascii")

    def u32(v):
        fo = fileoff(v)
        return struct.unpack_from("<I", d, fo)[0] if fo is not None else None

    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.detail = True
    md.skipdata = True
    ins = list(md.disasm(code, base))

    rows = []
    pend = {}
    pendoff = {}
    for i in range(len(ins)):
        it = ins[i]
        ops = it.op_str
        if it.mnemonic.startswith("ldr") and "[pc" in ops and \
                it.mnemonic != "ldr.w" or (it.mnemonic == "ldr.w" and "[pc" in ops):
            pass
        if it.mnemonic.startswith("ldr") and "[pc" in ops:
            try:
                imm = int(ops.split("#")[1].split("]")[0].strip(), 0)
            except Exception:
                continue
            pool = ((it.address + 4) & ~3) + imm
            v = u32(pool)
            dst = ops.split(",")[0].strip()
            pend[dst] = v
            pendoff[dst] = it.address
            continue
        if it.mnemonic.startswith("add") and "pc" in ops:
            dst = ops.split(",")[0].strip()
            if dst in pend and pend[dst] is not None:
                eff = ((it.address + 4) & ~3) + pend[dst]
                s = cstr(eff)
                if s and len(s) > 1:
                    # look ahead for the handler store
                    handler = None
                    for j in range(i + 1, min(i + 22, len(ins))):
                        it2 = ins[j]
                        o2 = it2.op_str
                        if it2.mnemonic.startswith("ldr") and "[pc" in o2:
                            try:
                                imm2 = int(o2.split("#")[1].split("]")[0].strip(), 0)
                            except Exception:
                                continue
                            p2 = ((it2.address + 4) & ~3) + imm2
                            w2 = u32(p2)
                            d2 = o2.split(",")[0].strip()
                            # next: ldr d2,[r6,d2]
                            if j + 1 < len(ins):
                                nx = ins[j + 1]
                                if nx.mnemonic == "ldr" and "r6" in nx.op_str and \
                                        d2 in nx.op_str:
                                    nm = slot2sym.get(GOT + (w2 or 0))
                                    if nm:
                                        handler = nm
                    rows.append((it.address, s, handler))
            pend.pop(dst, None)
            continue

    print("registration-like sites: %d" % len(rows))
    named = [r for r in rows if r[2]]
    print("of which with a resolved handler: %d" % len(named))
    print()
    print("=" * 78)
    print("ROUTE TABLE (uri -> handler), in registration order")
    print("=" * 78)
    for a, s, h in rows:
        if h is None:
            continue
        print("  0x%08x  %-34s  %s" % (a, s, h))

    print()
    print("=" * 78)
    print("sites whose handler could NOT be resolved (for honesty)")
    print("=" * 78)
    for a, s, h in rows:
        if h is None:
            print("  0x%08x  %s" % (a, s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
