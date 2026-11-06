#!/usr/bin/env python3
"""Two grounding checks for the "Linux -> servo firmware" question.

1) Does the controller-side binary we already hold carry SYMBOLS?  If
   libdataSvr.so is unstripped, its names are the search keys into the servo
   firmware, and that is what makes the reverse-lookup idea cheap.
2) Do the servo's own 97 OD objects intersect the zero-related VENDOR
   parameters (H01.17 / H0C.02 / H01.18)?  If yes, a plain SDO write may be
   able to trigger the encoder zeroing without touching firmware at all.
"""
import json
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def strings(d, n=5):
    return [m.group().decode("ascii", "replace")
            for m in re.finditer(rb"[\x20-\x7e]{%d,}" % n, d)]


# ---------- 1) symbols in libdataSvr.so ----------
p = os.path.join(ROOT, "libdataSvr.so.bin")
d = open(p, "rb").read()
print("=" * 74)
print("1) %s  (%d bytes)" % (os.path.basename(p), len(d)))
print("=" * 74)
print("  ELF? %s   class=%s  machine=0x%04x" % (
    d[:4] == b"\x7fELF",
    {1: "32-bit", 2: "64-bit"}.get(d[4] if len(d) > 4 else 0, "?"),
    struct.unpack_from("<H", d, 18)[0] if len(d) > 20 else 0))
secs = [s for s in (b".symtab", b".strtab", b".dynsym", b".debug_info",
                    b".debug_line", b".ARM.attributes", b".comment") if s in d]
print("  symbol/debug sections present: %s" % [s.decode() for s in secs])

s = strings(d)
print("  total strings>=5: %d" % len(s))
for pat in (r"updateEncoderData", r"calihome", r"innerEncoder", r"outEncoder",
            r"jointHomeState", r"conn_req_dir", r"WriteSDO|writeSdo|SDO",
            r"0x6064|6064", r"encoder", r"zero"):
    hits = [x for x in s if re.search(pat, x, re.I)]
    print("  %-24s : %4d  e.g. %s" % (pat, len(hits), hits[:3]))

# ---------- 2) OD objects vs zero-related vendor params ----------
print()
print("=" * 74)
print("2) servo OD objects  vs  vendor params")
print("=" * 74)
od = json.load(open(os.path.join(ROOT, "data/servo_fw_samples/od_328d8.json"),
                    encoding="utf-8"))
print("  od_328d8.json type: %s  len=%d" % (type(od).__name__, len(od)))
if isinstance(od, dict):
    k = list(od)[:3]
    print("  first keys: %s" % k)
    print("  sample   : %s" % json.dumps(od[k[0]], ensure_ascii=False)[:300])
elif isinstance(od, list):
    print("  sample   : %s" % json.dumps(od[0], ensure_ascii=False)[:300])

hp = json.load(open(os.path.join(ROOT, "data/servo_fw_samples/hparam_map.json"),
                    encoding="utf-8"))
print()
print("  hparam_map.json type: %s  len=%d" % (type(hp).__name__, len(hp)))
items = list(hp.items()) if isinstance(hp, dict) else list(enumerate(hp))
print("  sample: %s" % json.dumps(items[0], ensure_ascii=False)[:200])

# look for zero-related vendor params
if isinstance(hp, dict):
    pairs = [(k, v) for k, v in hp.items()]
else:
    pairs = [(str(i), v) for i, v in enumerate(hp)]
print()
print("  -- vendor params whose H-code or value mentions zero/encoder --")
for k, v in pairs:
    blob = json.dumps({k: v}, ensure_ascii=False)
    if re.search(r"H01\.1[78]|H0C\.0[23]|\u6821\u96f6|\u7f16\u7801\u5668|\u96f6",
                 blob, re.I):
        print("     %s" % blob[:200])

# ---------- 3) the already-proven dead end, restated with a number ----------
print()
print("=" * 74)
print("3) how often do VENDOR indices appear in the servo firmware?")
print("=" * 74)
for name, rel in (("D8", "data/servo_fw_samples/elf/v328d8.bin"),
                  ("3150", "data/servo_fw_samples/elf/v3150.bin")):
    pl = open(os.path.join(ROOT, rel), "rb").read()
    tot = 0
    for idx in (0x200C, 0x2001, 0x2000, 0x200D):
        tot += sum(1 for i in range(0, len(pl) - 2, 2)
                   if struct.unpack_from("<H", pl, i)[0] == idx)
    print("  %-5s : raw halfword hits for 0x2000/0x2001/0x200C/0x200D = %d"
          % (name, tot))
print("  (see AGENTS.md \u00a723.2 - these are Thumb instruction-byte false "
      "positives, not real references)")
