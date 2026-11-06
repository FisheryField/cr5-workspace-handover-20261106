#!/usr/bin/env python3
"""libalgs_framework.so.bin : symbol table dump + alarm-related symbol hunt.

Positive control: the log line proves that the strings
  "algs/inc/alarms.h", "AlarmSysSetBit", "AlarmSysCheckAll",
  "algs/src/common/run.cpp", "ServoControl"
exist somewhere in the file.  Step 0 checks raw-byte presence of those
tokens BEFORE any symbol work, so a 0-hit symbol search cannot be mistaken
for "the tool is blind".
"""
import re
import struct
import sys

P = r"D:\mydata\workspace\data\libalgs_framework.so.bin"
data = open(P, "rb").read()
assert data[:4] == b"\x7fELF"

SH_FMT = "<IIIIIIIIII"
SYM_FMT = "<IIIBBH"
STT = {0: "NOTYPE", 1: "OBJECT", 2: "FUNC", 3: "SECTION", 4: "FILE",
       5: "COMMON", 6: "TLS", 10: "IFUNC"}


def load():
    (_t, _m, _v, _e, _ph, e_shoff, _fl, _eh, _phes, _phn, e_shentsize,
     e_shnum, e_shstrndx) = struct.unpack_from("<HHIIIIIHHHHHH", data, 16)
    secs = []
    for i in range(e_shnum):
        f = struct.unpack_from(SH_FMT, data, e_shoff + i * e_shentsize)
        secs.append(dict(name_off=f[0], type=f[1], flags=f[2], addr=f[3],
                         offset=f[4], size=f[5], link=f[6], info=f[7],
                         entsize=f[9]))
    shstr = secs[e_shstrndx]

    def nm(o):
        s = data[shstr["offset"] + o:]
        return s[:s.index(b"\0")].decode("ascii", "replace")
    for s in secs:
        s["name"] = nm(s["name_off"])
    return secs


def symbols(secs):
    out = []
    for s in secs:
        if s["type"] not in (2, 11):
            continue
        strt = secs[s["link"]]
        base = strt["offset"]
        n = s["size"] // 16 if s["entsize"] == 0 else s["size"] // s["entsize"]
        for i in range(n):
            off = s["offset"] + i * 16
            name_o, value, size, info, _o, shndx = struct.unpack_from(SYM_FMT, data, off)
            if name_o == 0:
                continue
            e = data[base + name_o:]
            name = e[:e.index(b"\0")].decode("ascii", "replace")
            out.append(dict(name=name, value=value, size=size,
                            type=STT.get(info & 0xF, "?"), bind=info >> 4,
                            shndx=shndx, tab=s["name"]))
    return out


def main():
    print("=" * 78)
    print("0) POSITIVE CONTROL - raw byte presence of known log tokens")
    print("=" * 78)
    for tok in [b"algs/inc/alarms.h", b"AlarmSysSetBit", b"AlarmSysCheckAll",
                b"algs/src/common/run.cpp", b"ServoControl",
                b"algs_framework.cpp", b"algs_framework_get_ready_status",
                b"algs/src/common/command.cpp"]:
        n = data.count(tok)
        print("  %-42s raw hits=%d" % (tok.decode(), n))

    secs = load()
    syms = symbols(secs)
    print()
    print("symbols parsed: %d" % len(syms))

    print()
    print("=" * 78)
    print("1) symbols matching alarm / Alarm / CheckAll")
    print("=" * 78)
    seen = set()
    for s in syms:
        if not re.search(r"alarm", s["name"], re.I):
            continue
        k = (s["name"], s["value"], s["tab"])
        if k in seen:
            continue
        seen.add(k)
        print("  %-10s %-8s 0x%08x size=%-6d shndx=%-3d %s"
              % (s["tab"], s["type"], s["value"], s["size"], s["shndx"], s["name"]))

    print()
    print("=" * 78)
    print("2) symbols whose name contains gSysParams / gActualPosition /"
          " gRobotAxisMove / nextPos")
    print("=" * 78)
    for pat in [r"gSysParams", r"gActualPosition", r"gRobotAxisMove",
                r"nextPos", r"runQueuedCmd", r"gCmdFinishFlag", r"gRobotPrfMode"]:
        print("  --- %s ---" % pat)
        cnt = 0
        for s in syms:
            if re.search(pat, s["name"]):
                print("    %-10s %-8s 0x%08x size=%-6d %s"
                      % (s["tab"], s["type"], s["value"], s["size"], s["name"]))
                cnt += 1
        if cnt == 0:
            print("    (no symbol match)")

    print()
    print("=" * 78)
    print("3) FILE symbols (which translation units were compiled in)")
    print("=" * 78)
    files = sorted({s["name"] for s in syms if s["type"] == "FILE"})
    for f in files:
        print("  %s" % f)
    print("  total FILE symbols: %d" % len(files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
