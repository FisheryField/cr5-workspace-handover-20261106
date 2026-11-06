#!/usr/bin/env python3
"""Feature diff v2 - with a real filter on what counts as a STRING.

v1 set-compared every printable run >= 6 chars and produced 948 "D8-only
strings" that were almost all Thumb code bytes which happen to be printable
(e.g. '"DOB2$P', 'q(hAA!&').  Same failure class as the earlier CSV tests.

Filter applied here: a real string must
  * be >= 8 chars,
  * have >= 70% of its characters in [A-Za-z0-9 _.,:;%()/\-+=]
  * contain at least one lowercase letter OR at least one space
That keeps vendor strings such as "Position Actual Value" and drops code noise.
Positive controls: the two version strings, plus 'TxPDO assign' /
'Position Actual Value' from the OD name table, must all survive the filter.
"""
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES = [("D8", "data/servo_fw_samples/elf/v328d8.bin"),
          ("3150", "data/servo_fw_samples/elf/v3150.bin")]
GOOD = re.compile(r"^[A-Za-z0-9 _.,:;%()/\-+=@\[\]{}<>!?'\"#&*|~^$]{8,}$")
KEEPCH = re.compile(r"[A-Za-z0-9 _.,:;%()/\-+=]")


def payload(p):
    d = open(p, "rb").read()
    if d[:4] == bytes.fromhex("d4c3b2a1"):
        d = d[0x20:]
    return d


def real_strings(d):
    out = set()
    for m in re.finditer(rb"[\x20-\x7e]{8,}", d):
        s = m.group().decode("ascii", "replace")
        if not GOOD.match(s):
            continue
        frac = len(KEEPCH.findall(s)) / len(s)
        if frac < 0.70:
            continue
        if not (re.search(r"[a-z]", s) or " " in s):
            continue
        out.add(s)
    return out


def main():
    data = {t: payload(os.path.join(ROOT, rel)) for t, rel in IMAGES}
    S = {t: real_strings(data[t]) for t, _ in IMAGES}

    print("=" * 78)
    print("POSITIVE CONTROLS (must survive the filter)")
    print("=" * 78)
    ok = True
    for t, d in data.items():
        for probe in (b"DS.3.2.D.8", b"DS.3.1.5.0", b"TxPDO assign",
                      b"Position Actual Value", b"Modes of Operation"):
            found = any(probe.decode() in s for s in S[t])
            raw = d.find(probe) >= 0
            if raw:
                print("  %-5s raw=%-5s kept=%-5s  %s"
                      % (t, raw, found, probe.decode()))
                if not found:
                    ok = False
    print("  controls: %s" % ("PASS" if ok else "FAIL (filter too strict)"))
    if not ok:
        return 2

    print()
    print("  real-string counts: %s" % {t: len(S[t]) for t in S})
    only = {}
    for t in S:
        o = [x for x in S if x != t][0]
        only[t] = sorted(S[t] - S[o])
        print("  strings only in %-5s : %d" % (t, len(only[t])))

    for t in ("D8", "3150"):
        print()
        print("=" * 78)
        print("STRINGS ONLY IN %s (%d)" % (t, len(only[t])))
        print("=" * 78)
        for x in only[t]:
            print("   %s" % x)

    # vector table
    print()
    print("=" * 78)
    print("VECTOR TABLE (non-zero = handler exists)")
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
