#!/usr/bin/env python3
"""Open up libdataSvr.so: ELF layout, symbol table, DWARF string pool.

Why this is the entry point for the "Linux data chain -> servo firmware" plan:
  * DataSubProcess::caliHome()            is the handler that runs when the
    operator presses the zero-calibration button
  * DataSubProcess::updateEncoderData()   is the one that logs
    "servo calihome not done" / "servo calihome done"
  * DataSubProcess::readCurrentEncoder()  is an HTTP endpoint that reads the
    current encoder
  * DataSubProcess::getEncoderValue(u8)
Reading those gives the exact OD indices the master exchanges during
calibration, plus the value it expects - and that index set is exactly what the
servo firmware's dispatcher maps onto struct offsets.

This tool only reports structure; disassembly comes next.  The file is claimed
to carry .symtab/.strtab/.dynsym/.debug_info/.debug_line, so names should be
available without guesswork.  A positive control asserts that the four function
names above are actually present, and the tool aborts otherwise rather than
printing a misleadingly empty result.
"""
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "libdataSvr.so.bin")

SH_FMT = "<IIIIIIIIII"          # 40 bytes, Elf32_Shdr
SYM_FMT = "<IIIBBH"             # 16 bytes, Elf32_Sym
SHN = ["NULL", "PROGBITS", "SYMTAB", "STRTAB", "RELA", "HASH", "DYNAMIC",
       "NOTE", "NOBITS", "REL", "SHLIB", "DYNSYM"]
STT = {0: "NOTYPE", 1: "OBJECT", 2: "FUNC", 3: "SECTION", 4: "FILE",
       5: "COMMON", 6: "TLS"}


def load():
    d = open(P, "rb").read()
    assert d[:4] == b"\x7fELF", "not an ELF"
    assert d[4] == 1, "not 32-bit"
    (e_type, e_machine, _v, e_entry, e_phoff, e_shoff, _fl, _eh,
     _phentsize, _phnum, e_shentsize, e_shnum, e_shstrndx) = \
        struct.unpack_from("<HHIIIIIHHHHHH", d, 16)
    secs = []
    for i in range(e_shnum):
        f = struct.unpack_from(SH_FMT, d, e_shoff + i * e_shentsize)
        secs.append(dict(name_off=f[0], type=f[1], flags=f[2], addr=f[3],
                         offset=f[4], size=f[5], link=f[6], info=f[7],
                         align=f[8], entsize=f[9]))
    # section-name string table
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
        if s["type"] not in (2, 11):       # SYMTAB / DYNSYM
            continue
        strt = secs[s["link"]]
        base = strt["offset"]
        n = s["size"] // 16 if s["entsize"] == 0 else s["size"] // s["entsize"]
        for i in range(n):
            off = s["offset"] + i * 16
            if off + 16 > len(d):
                break
            name_o, value, size, info, other, shndx = struct.unpack_from(SYM_FMT, d, off)
            if name_o == 0:
                continue
            e = d[base + name_o:]
            name = e[:e.index(b"\0")].decode("ascii", "replace")
            out.append(dict(name=name, value=value, size=size,
                            type=STT.get(info & 0xF, "?"), bind=info >> 4,
                            shndx=shndx, tab=s["name"]))
    return out


def demangle(name):
    """Only enough C++ demangling to read the DataSubProcess methods."""
    m = re.match(r"^_ZN(\d+)(\w+)(.*)E$", name)
    if not m:
        return name
    rest = m.group(3)
    parts = []
    while rest and re.match(r"^\d", rest):
        k = re.match(r"^(\d+)", rest)
        n = int(k.group(1))
        parts.append(rest[len(k.group(1)):len(k.group(1)) + n])
        rest = rest[len(k.group(1)) + n:]
    cls = m.group(2)
    if parts:
        meth = parts[-1]
        args = parts[:-1]
        return "%s::%s(%s)" % (cls, meth, ", ".join(args))
    return "%s" % cls


def main():
    d, secs = load()
    print("=" * 78)
    print("1) ELF sections  (%d total, file %d bytes)" % (len(secs), len(d)))
    print("=" * 78)
    for s in secs:
        if s["size"] or s["name"] in ("NULL",):
            print("  %-20s type=%-8s addr=0x%08x off=0x%08x size=0x%08x"
                  % (s["name"], SHN[s["type"]] if s["type"] < len(SHN) else s["type"],
                     s["addr"], s["offset"], s["size"]))

    syms = symtab(d, secs)
    print()
    print("  symbols parsed: %d" % len(syms))

    print()
    print("=" * 78)
    print("2) POSITIVE CONTROL - the four functions this plan depends on")
    print("=" * 78)
    want = ["caliHome", "updateEncoderData", "getEncoderValue",
            "readCurrentEncoder"]
    ok = True
    for w in want:
        hits = [s for s in syms if w in s["name"]]
        print("  %-20s : %d symbol(s)" % (w, len(hits)))
        for h in hits[:4]:
            print("       0x%08x  size %-6d %-8s %s"
                  % (h["value"] & ~1, h["size"], h["type"], demangle(h["name"])))
        if not hits:
            ok = False
    if not ok:
        print("  !! CONTROL FAILED - abort")
        return 2

    print()
    print("=" * 78)
    print("3) names worth knowing (encoder/home/zero/cali/servo/slave)")
    print("=" * 78)
    pat = re.compile(r"encoder|home|zero|cali|servo|slave|position|offset",
                     re.I)
    seen = set()
    for s in syms:
        if s["type"] != "FUNC":
            continue
        dm = demangle(s["name"])
        if not pat.search(dm):
            continue
        if dm in seen:
            continue
        seen.add(dm)
        print("  0x%08x  size %-6d %s" % (s["value"] & ~1, s["size"], dm))

    print()
    print("=" * 78)
    print("4) DWARF: what debug sections exist, and the source files named")
    print("=" * 78)
    dbg = [s for s in secs if s["name"].startswith(".debug")]
    for s in dbg:
        print("  %-20s size 0x%x" % (s["name"], s["size"]))
    # .debug_str is a NUL-separated pool: cheap way to read identifiers
    ds = next((s for s in secs if s["name"] == ".debug_str"), None)
    if ds:
        blob = d[ds["offset"]:ds["offset"] + ds["size"]]
        strs = [x.decode("ascii", "replace") for x in blob.split(b"\0") if x]
        print("  .debug_str identifiers: %d" % len(strs))
        hits = [x for x in strs
                if re.search(r"encoder|home|zero|cali|Cali|Home|Zero|Offset|"
                             r"slave|Slave", x)]
        print("  interesting identifiers (%d):" % len(hits))
        for x in sorted(set(hits))[:120]:
            print("     %s" % x)
    else:
        print("  no .debug_str")

    print()
    try:
        import elftools  # noqa: F401
        print("  pyelftools: AVAILABLE (full DWARF parsing possible)")
    except ImportError:
        print("  pyelftools: not installed (would need a hand-written "
              ".debug_line parser for line numbers)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
