#!/usr/bin/env python3
"""Feature diff v3 - the string filter that actually isolates real phrases.

v1: every printable run >= 6 chars         -> 948 "D8-only strings", all code noise
v2: +70% dense charset + (lowercase|space)-> still leaked 'q(hAA!&', '"DK"Lr,XDDDA'
v3 (this): a PHRASE string must
      * match [A-Za-z0-9 ._/-]{8,}   (no quotes, $, ( ) , : ; ! & etc.)
      * have >= 50% lowercase among its LETTERS
Real vendor phrases satisfy this; Thumb code bytes rendered as ASCII do not
(they are symbol-dense and case-chaotic).

Version tokens such as DS.3.1.5.0 are all-uppercase, so they are NOT expected to
survive the phrase filter and are checked separately by raw byte search.
"""
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES = [("D8", "data/servo_fw_samples/elf/v328d8.bin"),
          ("3150", "data/servo_fw_samples/elf/v3150.bin")]
CHARSET = re.compile(r"^[A-Za-z0-9 ._/\-]{8,}$")


def payload(p):
    d = open(p, "rb").read()
    if d[:4] == bytes.fromhex("d4c3b2a1"):
        d = d[0x20:]
    return d


def phrase_strings(d):
    out = set()
    for m in re.finditer(rb"[\x20-\x7e]{8,}", d):
        s = m.group().decode("ascii", "replace")
        if not CHARSET.match(s):
            continue
        letters = [c for c in s if c.isalpha()]
        if not letters:
            continue
        if sum(1 for c in letters if c.islower()) / len(letters) < 0.50:
            continue
        out.add(s)
    return out


def main():
    data = {t: payload(os.path.join(ROOT, rel)) for t, rel in IMAGES}
    S = {t: phrase_strings(data[t]) for t, _ in IMAGES}

    print("=" * 78)
    print("POSITIVE CONTROLS (phrase filter)")
    print("=" * 78)
    ok = True
    for probe in ("TxPDO assign", "Position Actual Value", "Modes of Operation",
                  "Analogue Input Scaling Integer", "Motor rated current"):
        line = "  %-30s" % probe
        for t in ("D8", "3150"):
            kept = any(probe in s for s in S[t])
            line += "  %s=%s" % (t, kept)
            ok &= kept
        print(line)
    print("  phrase controls: %s" % ("PASS" if ok else "FAIL"))
    # version tokens by raw search
    for t, ver in (("D8", b"DS.3.2.D.8"), ("3150", b"DS.3.1.5.0")):
        print("  raw version token in %-5s : %s" % (t, data[t].find(ver) >= 0))
    if not ok:
        return 2

    print()
    print("  phrase-string counts: %s" % {t: len(S[t]) for t in S})
    only = {}
    for t in S:
        o = [x for x in S if x != t][0]
        only[t] = sorted(S[t] - S[o])
        print("  only in %-5s : %d" % (t, len(only[t])))

    for t in ("D8", "3150"):
        print()
        print("=" * 78)
        print("PHRASE STRINGS ONLY IN %s (%d)" % (t, len(only[t])))
        print("=" * 78)
        for x in only[t]:
            print("   %s" % x)

    print()
    print("=" * 78)
    print("VECTOR TABLE")
    print("=" * 78)
    NAMES = ["SP", "Reset", "NMI", "HardFault", "MemManage", "BusFault",
             "UsageFault", "-", "-", "-", "-", "SVC", "DebugMon", "-",
             "PendSV", "SysTick"]
    tbl = {t: [struct.unpack_from("<I", data[t], 4 * i)[0]
               for i in range(0x150 // 4)] for t in data}
    for i in range(len(tbl["D8"])):
        a, b = tbl["D8"][i], tbl["3150"][i]
        if a == 0 and b == 0:
            continue
        nm = NAMES[i] if i < len(NAMES) else "IRQ%d" % (i - 16)
        note = ""
        if (a == 0) != (b == 0):
            note = "  <<< PRESENT IN ONE BUILD ONLY"
        elif a != b:
            note = "  (both present, different target)"
        print("  %3d  %-12s  D8=0x%08x  3150=0x%08x%s" % (i, nm, a, b, note))
    print("  non-zero entries: %s" % {t: sum(1 for v in tbl[t] if v) for t in tbl})
    return 0


if __name__ == "__main__":
    sys.exit(main())
