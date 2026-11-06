#!/usr/bin/env python3
"""Generate a patched CR5 servo 3.1.5.0 FoE package (DEFAULT: dry-run only).

WHAT THE PATCH DOES
-------------------
The 3.1.5.0 position chain adds one arithmetic term that 3.2.D.8 does not have.
Both builds were read instruction by instruction at the line that produces
field +0x234 (which feeds the conversion function whose result becomes +0x238,
i.e. object 0x6064 "position actual value"):

    3.2.D.8  0x080255E0  ldr    r0,[sp,#0x18]
             0x080255E2  ldr    r0,[r0,#0x10]
             0x080255E4  ldr.w  r1,[r4,#0xb0]      ; normalize result
             0x080255E8  add    r1,r0              ; r1 = normalize + obj->0x10
             0x080255EA  ldr    r0,[sp,#0x14]
             0x080255EC  str.w  r1,[r0,#0x234]     ; +0x234 = r1
                                                       TWO source terms

    3.1.5.0  0x08024AF4  ldr    r0,[sp,#0x14]
             0x08024AF6  ldr    r0,[r0,#0x10]
             0x08024AF8  ldr.w  r1,[r5,#0xa8]      ; normalize result
             0x08024AFC  add    r0,r1              ; r0 = normalize + obj->0x10
             0x08024AFE  ldr    r1,[pc,#0xb0]      ; r1 = &0x20003DB0
             0x08024B00  ldr    r1,[r1,#0x18]      ; r1 = correction   <-- EXTRA
             0x08024B02  add    r1,r0              ; r1 = correction + r0
             0x08024B04  str.w  r1,[sb,#0x234]     ; +0x234 = r1
                                                       THREE source terms

So the extra term is `[0x20003DB0+0x18]`.  The patch makes the 3150 line
compute exactly what the D8 line computes, by replacing the three instructions
that introduce the term with a register move and two NOPs:

    08024AFE  2c 49        ldr  r1,[pc,#0xb0]   ->  01 46   mov r1, r0
    08024B00  89 69        ldr  r1,[r1,#0x18]   ->  00 bf   nop
    08024B02  01 44        add  r1,r0           ->  00 bf   nop
    08024B04  str.w r1,[sb,#0x234]            unchanged, 4-byte boundary intact

    r1 = r0 = normalize + obj->0x10   == the D8 value of +0x234.

*** THE BYTE ORDER OF THAT MOVE MATTERS AND WAS WRONG IN THIS TOOL'S FIRST
    VERSION. ***  `mov r1, r0` is halfword 0x4601, i.e. bytes `01 46`.
    The first version wrote `08 46`, which decodes as `mov r0, r1` - it would
    have stored the CORRECTION term as the position result, a wrong patch that
    still passes a naive "did the bytes change" check.  See
    tools/servo_patch_review.py (section 3 decodes all three candidates) and
    tools/servo_patch_verify3.py, which re-derives the required move from the
    surrounding code rather than trusting this constant.

WHY REMOVING THE TERM IS A LEGITIMATE STATE, NOT A HACK
------------------------------------------------------
The firmware itself contains a path in which the term is zero: immediately
before this line,

    0x08024AE6  ldr   r0,[pc,#0xc4]        ; = 0x20000020
    0x08024AE8  ldrh  r0,[r0]
    0x08024AEA  cmp   r0,#1
    0x08024AEC  bne   0x08024af4
    0x08024AEE  movs  r0,#0
    0x08024AF0  ldr   r1,[pc,#0xbc]        ; = 0x20003db0
    0x08024AF2  str   r0,[r1,#0x18]        ; correction := 0

so "correction == 0" is a mode the vendor wrote on purpose.  The patch simply
holds the position line in that mode permanently, without touching the state
machine that produces the term (8 write sites) or its other seven readers.

PACKAGE LAYOUT (verified identical between the vendor D8 file and the
self-made 3.1.5.0 file, so re-signing is legitimate) - tools/pkg_header_cmp.py:
    @0x00  d4 c3 b2 a1
    @0x04  MD5(payload)[0:12]
    @0x10  MD5(payload)[12:16]
    @0x14  len(payload) u32 LE
    @0x18  00 00 00 08
    @0x1c  ff ff ff ff
    @0x20  payload

LOAD ADDRESS (corrected 2026-09-24, tools/pkg_load_verdict.py)
    Both payloads load at 0x08010000, proven by two independent 100.0000%
    byte overlays (3.1.5.0 payload vs 3.1.5.hex, D8 payload vs the D8 app hex),
    by the FoE region rule (0x08000000 would erase the bootloader), and by the
    reset vector decoding cleanly only at that base.  An earlier note in this
    tool claimed 0x08000000 and called the manifest wrong; that note was wrong.
    The PATCH OFFSET is unaffected (it is found by byte pattern), but the flash
    address relabels 0x08014AFE -> 0x08024AFE.

SAFETY
  * Default is DRY RUN - writes nothing.  Pass --apply to emit the package.
  * Refuses to run if the source package's payload MD5 does not match its header.
  * Refuses to run if the 6-byte pattern is not unique in the payload.
  * Disassembles the patched bytes and refuses to write unless they decode to
    exactly `mov r1, r0 ; nop ; nop`.
  * Never modifies the input file.
"""
import argparse
import hashlib
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from servo_img import make_md  # noqa: E402

SRC = "data/servo_fw_samples/CR5_Servo_ST_FOE_V3.1.5.0_UNVERIFIED.bin"
OUT = "servo_fw/CR5_Servo_ST_FOE_V3.1.5.0_PATCHED_no_correction.bin"

FLASH_BASE = 0x08000000
PAYLOAD_OFF = 0x20
PAYLOAD_LOAD = 0x08010000          # PROVEN - see docstring
PATCH_ADDR = 0x08024AFE            # payload offset 0x14AFE

# variant A: delete the term outright (6 bytes in, 6 bytes out)
OLD_A = bytes.fromhex("2c4989690144")          # ldr / ldr / add
NEW_A = bytes.fromhex("014600bf00bf")          # mov r1,r0 ; nop ; nop
# variant B: keep the two dead loads, only stop the add from using their result
OLD_B_OFF = 0x08024B02 - PAYLOAD_LOAD          # 0x14B02
OLD_B = bytes.fromhex("0144")                  # add r1,r0
NEW_B = bytes.fromhex("0146")                  # mov r1,r0
EXPECT_A = [("mov", "r1, r0"), ("nop", ""), ("nop", "")]
EXPECT_B = [("mov", "r1, r0")]

# 16-bit Thumb NOP is the halfword 0xBF00, which in little-endian byte order is
# `00 BF` - NOT `BF 00`.  Writing bf00 decodes as `lsls r7,r7,#2` (a real
# instruction that clobbers r7).  The other tempting encoding, 0x46C0, decodes
# here as `stm r0!,{r1,r2,r6}`.  The disassembly check below is what catches
# this class of mistake; never write patch bytes from memory.


def decode(code, addr, n):
    md = make_md()
    return [(i.mnemonic, i.op_str) for i in md.disasm(code[:n], addr)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="actually write the patched package (default: dry run)")
    ap.add_argument("--variant", choices=("A", "B"), default="A",
                    help="A = mov+nop+nop (default), B = single-byte mov")
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    out_path = args.out or (OUT if args.variant == "A"
                            else OUT.replace(".bin", "_min1byte.bin"))
    old = OLD_A if args.variant == "A" else OLD_B
    new = NEW_A if args.variant == "A" else NEW_B
    expect = EXPECT_A if args.variant == "A" else EXPECT_B
    off = (PATCH_ADDR - PAYLOAD_LOAD) if args.variant == "A" else OLD_B_OFF

    b = open(args.src, "rb").read()
    payload = b[PAYLOAD_OFF:]

    print("=== source ===")
    print("  %s  (%d bytes, payload %d)" % (args.src, len(b), len(payload)))
    hdr_md5 = b[4:16] + b[0x10:0x14]
    real_md5 = hashlib.md5(payload).digest()
    print("  header MD5 field : %s" % hdr_md5.hex())
    print("  actual MD5       : %s" % real_md5.hex())
    if hdr_md5 != real_md5:
        print("  !! header/actual MD5 MISMATCH - refusing to patch")
        return 2
    print("  header MD5 OK (package is self-consistent)")

    print()
    print("=== patch site (variant %s) ===" % args.variant)
    print("  payload offset 0x%x   flash 0x%08x" % (off, PAYLOAD_LOAD + off))

    # uniqueness of the FULL 6-byte pattern, whichever variant is used: if the
    # long pattern is not unique the short one is not either, and this is the
    # only cheap guard against patching the wrong place.
    hits = []
    i = payload.find(OLD_A)
    while i >= 0:
        hits.append(i)
        i = payload.find(OLD_A, i + 1)
    print("  6-byte pattern %s occurs %d time(s) at %s"
          % (OLD_A.hex(" "), len(hits),
             " ".join("0x%x" % h for h in hits)))
    if len(hits) != 1 or hits[0] != (PATCH_ADDR - PAYLOAD_LOAD):
        print("  !! pattern is not unique / not where expected - refusing")
        return 2

    cur = payload[off:off + len(old)]
    print("  expect : %s" % old.hex(" "))
    print("  found  : %s" % cur.hex(" "))
    if cur != old:
        print("  !! content mismatch - refusing to patch")
        return 2

    # build the candidate payload FIRST: the disassembly check must look at the
    # PATCHED bytes.  (An earlier revision of this gate decoded `payload`, i.e.
    # the untouched source, and therefore compared the original instruction
    # sequence against the expected patched one - it rejected every patch.)
    cand = bytearray(payload)
    cand[off:off + len(new)] = new

    pre = decode(payload[off - 8:off + 8 + len(new)],
                 PAYLOAD_LOAD + off - 8, 8 + len(new))
    post = decode(bytes(cand[off:off + len(new)]), PAYLOAD_LOAD + off, len(new))
    tail = decode(payload[off + len(old):off + len(old) + 8],
                  PAYLOAD_LOAD + off + len(old), 8)

    print()
    print("=== disassembly check (mandatory: encoding by memory is how the")
    print("    first version of this tool produced a wrong patch) ===")
    print("  before:")
    for m, o in pre:
        print("      %-8s %s" % (m, o))
    print("  after (patched bytes decode to):")
    for m, o in post:
        print("      %-8s %s" % (m, o))
    print("  tail after the patched window (must be unchanged):")
    for m, o in tail:
        print("      %-8s %s" % (m, o))
    if post != expect:
        print("  !! patched bytes decode to %r, expected %r - refusing"
              % (post, expect))
        return 2
    if tail[0][0] not in ("str", "str.w"):
        print("  !! the instruction after the window is no longer a store - refusing")
        return 2
    print("  OK: decodes to %s and the following store is intact"
          % " ; ".join("%s %s" % t for t in post))

    new_payload = bytearray(payload)
    new_payload[off:off + len(new)] = new
    assert bytes(new_payload) == bytes(cand)
    changed = [k for k in range(off, off + len(old)) if payload[k] != new_payload[k]]
    print()
    print("  bytes actually changed : %d  (%s)"
          % (len(changed), " ".join("0x%x" % c for c in changed)))

    new_md5 = hashlib.md5(bytes(new_payload)).digest()
    header = (bytes.fromhex("d4c3b2a1")
              + new_md5[:12]
              + new_md5[12:16]
              + struct.pack("<I", len(new_payload))
              + bytes.fromhex("00000008")
              + bytes.fromhex("ffffffff"))
    out = header + bytes(new_payload)

    print()
    print("=== result ===")
    print("  new payload MD5    : %s" % new_md5.hex())
    print("  new payload length : %d (0x%x)  [unchanged: %s]"
          % (len(new_payload), len(new_payload), len(new_payload) == len(payload)))
    print("  new package bytes  : %d" % len(out))
    print("  MD5(package)       : %s" % hashlib.md5(out).hexdigest())
    print("  SHA-256(package)   : %s" % hashlib.sha256(out).hexdigest())

    if not args.apply:
        print()
        print("  DRY RUN - nothing written.  Re-run with --apply to emit")
        print("  %s" % out_path)
        return 0

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(out)
    print()
    print("  WROTE %s (%d bytes)" % (out_path, len(out)))

    chk = open(out_path, "rb").read()
    cp = chk[PAYLOAD_OFF:]
    print("  read-back payload MD5 : %s  %s"
          % (hashlib.md5(cp).hexdigest(),
             "OK" if hashlib.md5(cp).digest() == new_md5 else "MISMATCH"))
    print("  read-back patch bytes : %s  %s"
          % (cp[off:off + len(new)].hex(" "),
             "OK" if cp[off:off + len(new)] == new else "MISMATCH"))
    print("  read-back decode      : %s"
          % " ; ".join("%s %s" % t for t in decode(cp[off:off + len(new)],
                                                   PAYLOAD_LOAD + off, len(new))))
    # the rest of the payload must be byte-identical to the source
    diffs = sum(1 for k in range(len(payload)) if payload[k] != cp[k])
    print("  payload bytes differing from source : %d (expected %d)"
          % (diffs, len(changed)))
    return 0 if diffs == len(changed) else 2


if __name__ == "__main__":
    sys.exit(main())
