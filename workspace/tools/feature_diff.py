#!/usr/bin/env python3
"""FEATURE-level presence/absence diff between the two servo builds.

Motivation (from tools/periph_probe2.py + tim_presence.py): the two images are
only 34.9% byte-equal with 253 structural shift regions, so "function X differs"
is worthless as evidence.  The only signals that survive that noise are whole
FEATURES present in one build and absent in the other.

Two such signals are extracted here:

  A) STRING SET DIFF - every printable run >= 6 chars, set-compared.  Error
     messages, subsystem names and protocol constants are the classic feature
     fingerprint of a stripped firmware.  Positive control: the version strings
     DS.3.1.5.0 / DS.3.2.D.8 must appear in their own build.

  B) VECTOR TABLE - the first ~0x150 bytes are the Cortex-M vector table; an
     entry that is non-zero in one build and zero in the other means an
     interrupt handler exists in one build only = a whole peripheral feature
     enabled in one build only.  Positive control: SP and Reset must be
     non-zero in both.
"""
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES = [("D8", "data/servo_fw_samples/elf/v328d8.bin", b"DS.3.2.D.8"),
          ("3150", "data/servo_fw_samples/elf/v3150.bin", b"DS.3.1.5.0")]
LOAD = 0x08010000


def payload(p):
    d = open(p, "rb").read()
    if d[:4] == bytes.fromhex("d4c3b2a1"):
        d = d[0x20:]
    return d


def strings(d, n=6):
    return {m.group().decode("ascii", "replace")
            for m in re.finditer(rb"[\x20-\x7e]{%d,}" % n, d)}


def main():
    data = {}
    for tag, rel, ver in IMAGES:
        d = payload(os.path.join(ROOT, rel))
        data[tag] = dict(d=d, ver=ver)

    # ---------- positive control ----------
    print("=" * 78)
    print("POSITIVE CONTROL: version strings")
    print("=" * 78)
    ok = True
    for tag, rel, ver in IMAGES:
        d = data[tag]["d"]
        hit = d.find(ver) >= 0
        print("  %-5s contains its own version string %-14s : %s"
              % (tag, ver.decode(), hit))
        ok &= hit
        other = [v for t2, _, v in IMAGES if t2 != tag]
        for o in other:
            print("        (also contains the other build's %-14s : %s)"
                  % (o.decode(), d.find(o) >= 0))
    if not ok:
        print("  !! control failed - abort")
        return 2

    # ---------- A) string set diff ----------
    print()
    print("=" * 78)
    print("A) STRING SET DIFF (runs >= 6 printable chars)")
    print("=" * 78)
    S = {t: strings(data[t]["d"]) for t, _, _ in IMAGES}
    print("  string counts: %s" % {t: len(S[t]) for t in S})
    only = {t: sorted(S[t] - S[[x for x in S if x != t][0]]) for t in S}
    for t in ("D8", "3150"):
        o = [x for x in S if x != t][0]
        print()
        print("  --- strings ONLY in %s (%d) ---" % (t, len(only[t])))
        for x in only[t][:120]:
            print("      %s" % x)
        if len(only[t]) > 120:
            print("      ... %d more" % (len(only[t]) - 120))

    # ---------- B) vector table ----------
    print()
    print("=" * 78)
    print("B) VECTOR TABLE  (non-zero entry = handler exists)")
    print("=" * 78)
    NAMES = ["SP", "Reset", "NMI", "HardFault", "MemManage", "BusFault",
             "UsageFault", "-", "-", "-", "-", "SVC", "DebugMon", "-",
             "PendSV", "SysTick"]
    tbl = {}
    for tag, _, _ in IMAGES:
        d = data[tag]["d"]
        n = 0x150 // 4
        tbl[tag] = [struct.unpack_from("<I", d, 4 * i)[0] for i in range(n)]
    print("  idx  name          D8          3150        note")
    for i in range(len(tbl["D8"])):
        a, b = tbl["D8"][i], tbl["3150"][i]
        if a == 0 and b == 0:
            continue                       # unused in both - not a feature diff
        nm = NAMES[i] if i < len(NAMES) else "IRQ%d" % (i - 16)
        note = ""
        if (a == 0) != (b == 0):
            note = "  <<< PRESENT IN ONE ONLY"
            ok = ok and False
        elif a != b:
            note = "  (both present, different handler)"
        print("  %3d  %-12s  0x%08x  0x%08x%s" % (i, nm, a, b, note))

    nz = {t: sum(1 for v in tbl[t] if v) for t in tbl}
    print("  non-zero entries: %s" % nz)
    print()
    print("OVERALL: %s" % ("ok" if ok else "see notes above"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
