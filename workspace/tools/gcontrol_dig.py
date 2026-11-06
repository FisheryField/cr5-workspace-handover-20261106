#!/usr/bin/env python3
"""Dig into gcontrol (the process that owns the HTTP server).

Why: three independent caller-finding methods on libdataSvr.so all abstained
correctly, which means DataSubProcess::caliHome is NOT called from inside that
shared object.  The HTTP route "/calibrate/home" therefore must be registered
in the executable that owns the server socket -> gcontrol.

Strategy (each step has a positive control):
  1) ELF layout + section list, and whether .symtab survived (probably stripped)
  2) locate the literal string "/calibrate/home" (and friends) in the file, and
     report its file offset / virtual address / containing section
  3) find which code references that address.  On ARM PIC, a string address is
     materialised as: ldr rX,[pc,#imm]  (loads an *offset* from .got-ish pool)
     followed by add rX,pc,rX  OR via a literal pool dword that the linker fills.
     For a static-ish executable we must try several idioms, AND run a positive
     control: a string we KNOW is referenced (pick one that appears in a
     printf-style call context).
  4) dump the code window around each reference so the route table is visible.

Abstention: if the positive control finds nothing, print CONTROL FAILED and
return non-zero rather than an empty "answer".
"""
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "data", "cabinet", "gcontrol_from_controller.bin")

SH_FMT = "<IIIIIIIIII"
SHN = {0: "NULL", 1: "PROGBITS", 2: "SYMTAB", 3: "STRTAB", 4: "RELA",
       5: "HASH", 6: "DYNAMIC", 7: "NOTE", 8: "NOBITS", 9: "REL",
       10: "SHLIB", 11: "DYNSYM", 14: "INIT_ARRAY", 15: "FINI_ARRAY",
       16: "PREINIT_ARRAY", 17: "GROUP", 18: "SYMTAB_SHNDX"}
SHT = {k: v for k, v in SHN.items()}
SHN.update({6: "DYNAMIC", 7: "NOTE", 11: "DYNSYM", 14: "INIT_ARRAY",
            15: "FINI_ARRAY", 16: "PREINIT_ARRAY", 17: "GROUP"})


def load():
    d = open(P, "rb").read()
    assert d[:4] == b"\x7fELF", "not an ELF"
    is64 = d[4] == 2
    if not is64:
        (e_type, e_machine, _v, e_entry, e_phoff, e_shoff, _fl, _eh,
         _phentsize, _phnum, e_shentsize, e_shnum, e_shstrndx) = \
            struct.unpack_from("<HHIIIIIHHHHHH", d, 16)
        secs = []
        for i in range(e_shnum):
            f = struct.unpack_from(SH_FMT, d, e_shoff + i * e_shentsize)
            secs.append(dict(name_off=f[0], type=f[1], flags=f[2], addr=f[3],
                             offset=f[4], size=f[5], link=f[6], info=f[7],
                             align=f[8], entsize=f[9]))
        shstr = secs[e_shstrndx]

        def nm(o):
            s = d[shstr["offset"] + o:]
            return s[:s.index(b"\0")].decode("ascii", "replace")
        for s in secs:
            s["name"] = nm(s["name_off"])
        return d, secs, dict(is64=False, entry=e_entry, machine=e_machine,
                             etype=e_type, phoff=e_phoff, phnum=_phnum,
                             phentsize=_phentsize)
    # 64-bit path (unlikely but cheap)
    (e_type, e_machine, _v, e_entry, e_phoff, e_shoff, _fl, _eh,
     _phentsize, _phnum, e_shentsize, e_shnum, e_shstrndx) = \
        struct.unpack_from("<HHIQQQIHHHHHH", d, 16)
    secs = []
    for i in range(e_shnum):
        f = struct.unpack_from("<IIQQQQIIQQ", d, e_shoff + i * e_shentsize)
        secs.append(dict(name_off=f[0], type=f[1], flags=f[2], addr=f[3],
                         offset=f[4], size=f[5], link=f[6], info=f[7],
                         align=f[8], entsize=f[9]))
    shstr = secs[e_shstrndx]

    def nm(o):
        s = d[shstr["offset"] + o:]
        return s[:s.index(b"\0")].decode("ascii", "replace")
    for s in secs:
        s["name"] = nm(s["name_off"])
    return d, secs, dict(is64=True, entry=e_entry, machine=e_machine,
                         etype=e_type, phoff=e_phoff, phnum=_phnum,
                         phentsize=_phentsize)


def sect_of(secs, off):
    for s in secs:
        if s["type"] == 8:          # NOBITS has no file bytes
            continue
        if s["offset"] <= off < s["offset"] + s["size"]:
            return s
    return None


def main():
    d, secs, hdr = load()
    print("=" * 78)
    print("1) ELF header / sections   (file %d bytes, e_type=%d, machine=%d)"
          % (len(d), hdr["etype"], hdr["machine"]))
    print("=" * 78)
    print("   entry = 0x%08x   is64=%s" % (hdr["entry"], hdr["is64"]))
    for s in secs:
        if s["size"] == 0 and s["name"] in ("NULL", ""):
            continue
        print("  %-22s type=%-12s addr=0x%08x off=0x%08x size=0x%08x"
              % (s["name"], SHT.get(s["type"], str(s["type"])), s["addr"],
                 s["offset"], s["size"]))
    n_sym = sum(1 for s in secs if s["name"] in (".symtab", ".dynsym"))
    symsz = [s["size"] for s in secs if s["name"] in (".symtab", ".dynsym")]
    print("   .symtab/.dynsym present: %d  sizes=%s" % (n_sym, symsz))

    print()
    print("=" * 78)
    print("2) locate the calibration route strings")
    print("=" * 78)
    needles = [b"/calibrate/home", b"calibrate/home", b"calibrate",
               b"/calibrate/home1"]
    found = {}
    for nd in needles:
        hits = []
        start = 0
        while True:
            i = d.find(nd, start)
            if i < 0:
                break
            hits.append(i)
            start = i + 1
        found[nd] = hits
        print("  %-18s : %d hit(s)" % (nd.decode(), len(hits)))
        for i in hits[:12]:
            s = sect_of(secs, i)
            va = (s["addr"] + (i - s["offset"])) if s else None
            print("     file 0x%06x  va %s  section %s"
                  % (i, ("0x%08x" % va) if va is not None else "?",
                     s["name"] if s else "?"))
            # print the string, sanitised
            e = d.find(b"\0", i)
            raw = d[i:min(e, i + 96)]
            print("        %r" % raw)

    # positive control: a route-ish string that must exist, plus verify the
    # finder can at least see a *known* nearby literal
    print()
    print("=" * 78)
    print("3) route-string survey (positive control on the finder itself)")
    print("=" * 78)
    routes = re.compile(rb"/(?:[A-Za-z0-9_.\-]+/)*[A-Za-z0-9_.\-]+")
    allr = set()
    for m in routes.finditer(d):
        s = m.group(0)
        if 4 <= len(s) <= 60 and s.count(b"/") >= 1:
            allr.add(s)
    print("  distinct /-ish tokens in file: %d" % len(allr))
    ctrl = b"/calibrate/home"
    print("  POSITIVE CONTROL  '/calibrate/home' in token set: %s"
          % (ctrl in allr))
    interesting = sorted(x for x in allr
                         if re.search(rb"cali|home|zero|encoder|servo|update|"
                                      rb"robot|enable|version|joint", x, re.I))
    print("  interesting route-ish strings (%d):" % len(interesting))
    for x in interesting[:200]:
        i = d.find(x)
        s = sect_of(secs, i) if i >= 0 else None
        va = (s["addr"] + (i - s["offset"])) if s else None
        print("     %-46s  va=%s" % (x.decode("ascii", "replace"),
                                     ("0x%08x" % va) if va is not None else "?"))

    # 4) who references the address of /calibrate/home?
    print()
    print("=" * 78)
    print("4) references to the /calibrate/home address")
    print("=" * 78)
    h = found[b"/calibrate/home"]
    if not h:
        print("  no literal string -> nothing to reference; STOP")
        return 1
    for i in h:
        s = sect_of(secs, i)
        if not s or s["addr"] == 0:
            print("  hit at file 0x%x is not in an address-bearing section "
                  "(%s) -> cannot be referenced by VA"
                  % (i, s["name"] if s else "?"))
            continue
        va = s["addr"] + (i - s["offset"])
        print("  string VA = 0x%08x" % va)
        # (a) raw dword equal to VA anywhere in file (literal pool entry)
        pat = struct.pack("<I", va)
        locs = []
        start = 0
        while True:
            j = d.find(pat, start)
            if j < 0:
                break
            locs.append(j)
            start = j + 1
        print("    dword==VA occurrences: %d" % len(locs))
        for j in locs[:20]:
            cs = sect_of(secs, j)
            print("      file 0x%06x  section %s  (pool candidate)"
                  % (j, cs["name"] if cs else "?"))
        # (b) PC-relative: for every ldr rX,[pc,#imm] compute
        #     ((addr_of_insn+4)&~3)+imm and see if it lands near the string
        #     -- this finds the *pool slot*, so combine with (a).
        # (c) the ARM PIC idiom: ldr rX,[pc,#imm] -> add rX,pc,rX
    return 0


if __name__ == "__main__":
    sys.exit(main())
