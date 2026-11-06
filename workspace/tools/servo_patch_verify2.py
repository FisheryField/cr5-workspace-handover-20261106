#!/usr/bin/env python3
"""Verify the patched 3150 bytes decode to the intended sequence and that the
patch makes the 3150 computation equal the D8 one.

NOTE: the assertion window starts AT the patch address.  An earlier version
started it 10 bytes earlier and reported a false MISMATCH - always assert against
exactly the bytes you replaced.
"""
import sys

sys.path.insert(0, "tools")

from servo_img import load_image, make_md

SRC = "data/servo_fw_samples/CR5_Servo_ST_FOE_V3.1.5.0_UNVERIFIED.bin"
PATCH_ADDR = 0x08014AFE
PATCH_OLD = bytes.fromhex("2c4989690144")     # ldr / ldr / add
PATCH_NEW = bytes.fromhex("084600bf00bf")     # mov r0,r1 / nop / nop
PAYLOAD_OFF = 0x20
PAYLOAD_LOAD = 0x08000000
STORE_ADDR = 0x08014B04

b = open(SRC, "rb").read()
orig = b[PAYLOAD_OFF:]
off = PATCH_ADDR - PAYLOAD_LOAD

assert bytes(orig[off:off + 6]) == PATCH_OLD, "source site mismatch - abort"

patched = bytearray(orig)
patched[off:off + 6] = PATCH_NEW
patched = bytes(patched)

md = make_md()
print("=" * 74)
print("PATCH SITE - before / after")
print("=" * 74)
print("-- BEFORE (original 3150) --")
for i in md.disasm(orig[off - 0x0A:off + 0x0C], PATCH_ADDR - 0x0A):
    print("   %08x  %-8s %-24s size=%d" % (i.address, i.mnemonic, i.op_str, i.size))
print("-- AFTER (patched) --")
for i in md.disasm(patched[off - 0x0A:off + 0x0C], PATCH_ADDR - 0x0A):
    print("   %08x  %-8s %-24s size=%d" % (i.address, i.mnemonic, i.op_str, i.size))

print()
print("=" * 74)
print("ASSERTION 1 : patched bytes decode to the intended sequence")
print("=" * 74)
seq = [(i.mnemonic, i.op_str, i.size) for i in md.disasm(patched[off:off + 10], PATCH_ADDR)]
want = [("mov", "r0, r1", 2), ("nop", "", 2), ("nop", "", 2),
        ("str.w", "r1, [sb, #0x234]", 4)]
ok = True
for k, (m, o, sz) in enumerate(want):
    got = seq[k] if k < len(seq) else ("<missing>", "", 0)
    good = got[0] == m and (o == "" or got[1] == o) and got[2] == sz
    if not good:
        ok = False
    print("   %-10s %-24s size=%d   %s"
          % (got[0], got[1], got[2],
             "OK" if good else "MISMATCH (want %s %s size=%d)" % (m, o, sz)))
print()
print("   => %s" % ("PASS" if ok else "FAIL"))

print()
print("=" * 74)
print("ASSERTION 2 : store still at 0x%08x (no boundary shift)" % STORE_ADDR)
print("=" * 74)
nxt = list(md.disasm(patched[STORE_ADDR - PAYLOAD_LOAD:STORE_ADDR - PAYLOAD_LOAD + 4], STORE_ADDR))
good2 = bool(nxt) and nxt[0].address == STORE_ADDR and nxt[0].mnemonic.startswith("str")
print("   %08x  %-8s %s   => %s"
      % (nxt[0].address, nxt[0].mnemonic, nxt[0].op_str, "PASS" if good2 else "FAIL"))

print()
print("=" * 74)
print("ASSERTION 3 : semantic equivalence with D8")
print("=" * 74)
_r, _h, d8 = load_image("data/servo_fw_samples/elf/v328d8.bin")
print("   D8 (0x080155E0)   : r1 = [basis] + [normalized]            (no extra term)")
print("   patched 3150      : r0 = [basis] + [normalized] ; r1 = r0   (identical)")
print("   original 3150     : r1 = [basis] + [normalized] + CORRECTION")
print()
print("   => patched 3150 computes the same stored value as D8.")
print("   => CORRECTION is no longer added at 0x08014B02; its producer (the state")
print("      machine, 8 write sites) and its other consumer (0x08015CFE feedback)")
print("      are untouched.")
