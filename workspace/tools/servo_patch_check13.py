#!/usr/bin/env python3
"""PATCH FEASIBILITY CHECK (1/3 + 3/3).

(1/3) register semantics: prove that at the patch site, `add r1,r0` computes
      exactly what the store needs, and that r1 carries no other live value.

(3/3) side effects: enumerate EVERY read of the value we intend to bypass
      (0x20003DB0 + 0x18) in the 3150 build, and classify each as
      "consumed by the position result" vs "feedback into the state machine".
      Removing the correction from the position sum is only safe if the state
      machine's own use of +0x18 is untouched (we NOP the consumer, not the
      producer).

Patch site (byte-accurate, 3150):
    08014AFE  2c 49     ldr   r1,[pc,#0xb0]    ; r1 = 0x20003DB0
    08014B00  89 69     ldr   r1,[r1,#0x18]    ; r1 = correction
    08014B02  01 44     add   r1,r0            ; r1 = r1 + r0
    08014B04  c9 f8 34 12  str.w r1,[sb,#0x234]
"""
import sys

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image, make_md
from servo_litmap import resolve_literals

P = "data/servo_fw_samples/elf/v3150.bin"
_r, _h, code = load_image(P)
md = make_md()
insns = list(md.disasm(code, FLASH_BASE))
byaddr = {i.address: i for i, _ in [(i, 0) for i in insns]}
idx = {i.address: k for k, i in enumerate(insns)}

print("=" * 78)
print("(1/3)  REGISTER SEMANTICS at the patch site")
print("=" * 78)
lo, hi = 0x08014AF4, 0x08014B0C
for i in insns:
    if lo <= i.address < hi:
        mark = "   <== patch window" if 0x08014AFE <= i.address < 0x08014B04 else ""
        print("  %08x  %-8s %-24s%s" % (i.address, i.mnemonic, i.op_str, mark))
print()
print("  dataflow claim:")
print("    r0 = [sp+0x14]->[+0x10] + [r5+0xA8]      (basis + normalized)  @08014AF4..08014AFC")
print("    r1 = [0x20003DB0+0x18]                   (correction)          @08014AFE..08014B00")
print("    r1 = r1 + r0                                                   @08014B02")
print("    [sb+0x234] = r1                                                @08014B04")
print()
print("  -> r1 after 0x08014AFC is DEAD (overwritten at 0x08014AFE), so replacing")
print("     0x08014AFE..0x08014B02 with `mov r1,r0` + 2x nop reproduces exactly")
print("     the store value the D8 build computes (r1 = basis+normalized).")

print()
print("=" * 78)
print("(3/3)  EVERY read of 0x20003DB0 + 0x18 in the 3150 build")
print("=" * 78)
lit = resolve_literals(P)
base_sites = sorted(a for a, (m, o, p, v) in lit.items() if v == 0x20003DB0)
reads = []
for a in base_sites:
    reg = lit[a][1].split(",")[0].strip()
    cur = {reg}
    for j in range(idx[a], min(len(insns), idx[a] + 5)):
        i = insns[j]
        if i.address <= a:
            continue
        if i.mnemonic in ("mov", "mov.w") and "," in i.op_str:
            d, s = [x.strip() for x in i.op_str.split(",")[:2]]
            if s in cur:
                cur.add(d)
                continue
        if "[" in i.op_str and "pc" not in i.op_str:
            inside = i.op_str.split("[", 1)[1]
            for c in cur:
                if not inside.startswith(c):
                    continue
                if "#0x18]" in i.op_str:
                    reads.append((i.address, i.mnemonic, i.op_str,
                                  "read" if i.mnemonic.startswith("ldr") else "WRITE"))
        if i.mnemonic.startswith(("ldr", "add", "sub")):
            d = i.op_str.split(",")[0].strip()
            if d in cur and d != reg:
                cur.discard(d)

print("  %d site(s):" % len(reads))
for a, m, o, k in sorted(reads):
    print("    %08x  %-5s %-9s %s" % (a, k, m, o))

print()
print("  classification of the READS:")
for a, m, o, k in sorted(reads):
    if k != "read":
        continue
    if 0x08014B00 == a:
        print("    %08x  -> position-result consumer   <== the one we intend to bypass" % a)
    else:
        print("    %08x  -> OTHER consumer (state machine feedback)" % a)
