#!/usr/bin/env python3
"""Independent verification of the 3.1.5.0 position patch (assertion based).

Every check below has a POSITIVE CONTROL: a known-present sample that the
detector must find.  This workspace has been burned five separate times by
searches that returned an empty result without saying so, so a detector that
cannot demonstrate it fires on a known case is not evidence of absence.

Checks
  V1  patch direction is re-derived from the code, not trusted:
      the store at +0x04 stores r1, and D8's line stores (normalize + obj->0x10),
      which in 3150 lives in r0 after 0x08024AFC.  So the patch MUST be
      `mov r1, r0` (01 46).  The verifier asserts the two candidate moves decode
      to different registers and that the shipped bytes are the right one.
  V2  r0's provenance read backwards: r0 = [[sp+0x14]+0x10] + [r5+0xA8].
  V3  r1 is free at the patch point: the very next instruction consumes and
      overwrites it (the store), so clobbering it changes nothing else.
  V4  no branch anywhere in the image targets the patched window.
  V5  the extra term's read sites: exactly one is bypassed, the rest are inside
      the state machine and untouched.
  V6  positive control for store detection: the single str.w to +0x234 is found.
  V7  positive control for branch detection: a known branch is found.
"""
import hashlib
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from servo_img import make_md  # noqa: E402
from capstone import CS_OP_IMM, CS_OP_MEM, CS_OP_REG  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V3150 = os.path.join(ROOT, "data/servo_fw_samples/elf/v3150.bin")
V328D8 = os.path.join(ROOT, "data/servo_fw_samples/elf/v328d8.bin")
PKG = os.path.join(ROOT, "servo_fw/CR5_Servo_ST_FOE_V3.1.5.0_PATCHED_no_correction.bin")
PKG_B = os.path.join(ROOT,
                     "servo_fw/CR5_Servo_ST_FOE_V3.1.5.0_PATCHED_no_correction_min1byte.bin")

LOAD = 0x08010000
WIN = [0x08024AFE, 0x08024B00, 0x08024B02]
STORE234 = 0x08024B04
STATE_LO, STATE_HI = 0x08025700, 0x08025E00
CORR_BASE = 0x20003DB0
CORR_OFF = 0x18

FAIL = []


def check(name, ok, detail=""):
    print("  [%s] %s%s" % ("PASS" if ok else "FAIL", name,
                           ("  -- " + detail) if detail else ""))
    if not ok:
        FAIL.append(name)


def payload(p):
    d = open(p, "rb").read()
    if d[:4] == bytes.fromhex("d4c3b2a1"):
        d = d[0x20:]
    return d


def lit(pl, i, imm):
    a = ((i + 4) & ~3) + imm
    return struct.unpack_from("<I", pl, a)[0] if a + 4 <= len(pl) else -1


def decode(code, addr, n=None):
    md = make_md()
    return [(i.mnemonic, i.op_str) for i in md.disasm(code[:n], addr)]


def branches(pl):
    """(site, target) for every control-flow instruction with an immediate
    target.  Positive control in V7 proves this detector fires at all."""
    md = make_md()
    md.detail = True
    out = []
    for ins in md.disasm(pl, LOAD):
        m = ins.mnemonic
        if not (m.startswith("b") or m.startswith("cb")):
            continue
        try:
            ops = ins.operands
        except Exception:
            continue
        if ops and ops[0].type == CS_OP_IMM:
            out.append((ins.address, ops[0].imm))
    return out


def corr_reads(pl):
    """Sites that read [0x20003DB0+0x18] - find the base literal, then the
    next access through the loaded register with displacement 0x18."""
    md = make_md()
    md.detail = True
    insns = list(md.disasm(pl, LOAD))
    idx = {}
    for k, ins in enumerate(insns):
        idx[ins.address] = k
    reads = []
    for k, ins in enumerate(insns):
        if not (ins.mnemonic.startswith("ldr") and "[pc" in ins.op_str):
            continue
        try:
            imm = int(ins.op_str.split("#")[1].split("]")[0].strip(), 0)
        except Exception:
            continue
        if lit(pl, ins.address - LOAD, imm) != CORR_BASE:
            continue
        reg = ins.op_str.split(",")[0].strip()
        for ins2 in insns[k + 1:k + 6]:
            try:
                ops = ins2.operands
            except Exception:
                break
            for op in ops:
                # CS_OP_MEM == 3.  Writing `op.type == 1` here (CS_OP_REG) made
                # this detector return 0 sites for a read that is plainly in the
                # listing - the V5 positive control is what caught it.
                if op.type == CS_OP_MEM and ins2.reg_name(op.mem.base) == reg \
                        and op.mem.disp == CORR_OFF:
                    reads.append((ins2.address, "W" if op.access & 2 else "r"))
            if any(op.type == CS_OP_MEM and ins2.reg_name(op.mem.base) == reg
                   for op in ops):
                break
    return reads


def store234(pl):
    hits = []
    for i in range(0, len(pl) - 4, 2):
        w = struct.unpack_from("<H", pl, i)[0]
        if (w & 0xFFF0) != 0xF8C0:
            continue
        w2 = struct.unpack_from("<H", pl, i + 2)[0]
        if (w2 & 0x0FFF) == 0x234:
            hits.append(i)
    return hits


def main():
    v = payload(V3150)
    d8 = payload(V328D8)

    print("=" * 78)
    print("V0  context: the two lines, re-read from the raw bytes")
    print("=" * 78)
    print("  3150 0x08024AF4..0x08024B04 :")
    for m, o in decode(v[0x14AF4:0x14B08], LOAD + 0x14AF4):
        print("      %-9s %s" % (m, o))
    print("  D8   0x080255E0..0x080255EC :")
    for m, o in decode(d8[0x155E0:0x155F0], LOAD + 0x155E0):
        print("      %-9s %s" % (m, o))
    d8_terms = [t for t in decode(d8[0x155E0:0x155F0], LOAD + 0x155E0)]
    check("V0.1 D8 line has no third addend (no ldr r1,[r1,#..] / add r1,r0 pair)",
          not any(m == "ldr" and o == "r1, [r1, #0x18]" for m, o in d8_terms))
    print()

    print("=" * 78)
    print("V1  the required move is re-derived, not trusted")
    print("=" * 78)
    a = decode(bytes.fromhex("0146"), LOAD + 0x14AFE)
    b = decode(bytes.fromhex("0846"), LOAD + 0x14AFE)
    print("  0146 -> %s %s" % a[0])
    print("  0846 -> %s %s" % b[0])
    check("V1.1 the two candidate encodings are different instructions",
          a[0] != b[0], "%s vs %s" % (a[0], b[0]))
    check("V1.2 required direction is `mov r1, r0` (source value is in r0)",
          a[0] == ("mov", "r1, r0"))
    check("V1.3 the previously shipped wrong encoding was `mov r0, r1`",
          b[0] == ("mov", "r0, r1"))
    print()

    print("=" * 78)
    print("V2  r0 provenance (read backwards from 0x08024AFC)")
    print("=" * 78)
    back = decode(v[0x14AF4:0x14AFE], LOAD + 0x14AF4)
    for m, o in back:
        print("      %-9s %s" % (m, o))
    check("V2.1 r0 = [sp+0x14] -> +0x10",
          back[0] == ("ldr", "r0, [sp, #0x14]") and back[1] == ("ldr", "r0, [r0, #0x10]"))
    check("V2.2 r1 = [r5+0xa8]",
          back[2] == ("ldr.w", "r1, [r5, #0xa8]"))
    check("V2.3 add r0, r1 makes r0 = the D8 quantity",
          back[3] == ("add", "r0, r1"))
    print()

    print("=" * 78)
    print("V3  r1 is free at the patch point")
    print("=" * 78)
    nxt = decode(v[0x14B04:0x14B0C], LOAD + 0x14B04)
    print("      next: %s %s" % nxt[0])
    check("V3.1 the instruction right after the window consumes r1 and is the "
          "store to +0x234",
          nxt[0] == ("str.w", "r1, [sb, #0x234]"))
    print("      -> r1 is written by the patch and immediately consumed; no other")
    print("         instruction between the window and the store can observe it.")
    print()

    print("=" * 78)
    print("V4  no branch targets the patched window")
    print("=" * 78)
    br = branches(v)
    print("      branch instructions found: %d" % len(br))
    check("V7/positive control: branch detector fires at all", len(br) > 5000,
          "%d branches" % len(br))
    check("V7/positive control: known branch bne -> 0x08024af4 is found",
          any(t == 0x08024AF4 for _, t in br))
    hits = [(s, t) for s, t in br if t in WIN]
    for s, t in hits:
        print("      !! 0x%08x -> 0x%08x" % (s, t))
    check("V4.1 zero branches target 0x08024AFE / 0x08024B00 / 0x08024B02",
          not hits, "%d of %d targets" % (len(br), len(br)))
    print()

    print("=" * 78)
    print("V5  readers of [0x%08x+0x%02x]" % (CORR_BASE, CORR_OFF))
    print("=" * 78)
    rd = corr_reads(v)
    in_state = lambda a2: STATE_LO <= a2 < STATE_HI          # noqa: E731
    for a2, d in rd:
        where = ("BYPASSED by the patch" if a2 == 0x08024B00 else
                 "the gate's own clear (untouched)" if a2 == 0x08024AF2 else
                 "inside the state machine (untouched)" if in_state(a2)
                 else "OUTSIDE - INVESTIGATE")
        print("      0x%08x  %s   %s" % (a2, d, where))
    reads = sorted(a2 for a2, d in rd if d == "r")
    writes = sorted(a2 for a2, d in rd if d == "W")
    print("      -> %d readers, %d writers, %d sites total"
          % (len(reads), len(writes), len(rd)))
    check("V5/positive control: the known read at 0x08024b00 is found",
          any(a2 == 0x08024B00 for a2, _ in rd))
    check("V5.1 the only reader outside the state machine is 0x08024b00 "
          "(the one the patch bypasses)",
          [a2 for a2 in reads if not in_state(a2)] == [0x08024B00],
          "%s" % [hex(a2) for a2 in reads if not in_state(a2)])
    check("V5.2 the only writer outside the state machine is 0x08024af2 "
          "(the gate's conditional clear, well above the patched window)",
          [a2 for a2 in writes if not in_state(a2)] == [0x08024AF2],
          "%s" % [hex(a2) for a2 in writes if not in_state(a2)])
    check("V5.3 every other site is inside the state machine region and untouched",
          all(a2 == 0x08024B00 or a2 == 0x08024AF2 or in_state(a2)
              for a2, _ in rd))
    check("V5.4 the patched window itself contains no access to +0x18",
          not any(0x08024AFE <= a2 < 0x08024B04 for a2, _ in rd
                  if not (a2 == 0x08024B00)))
    print("      (NOTE: an earlier session note claimed 2 readers total; the real")
    print("       count is %d readers + %d writer inside the state machine.  The" % (len(reads) - 1, len(writes)))
    print("       conclusion is unchanged - all the others are the state machine's")
    print("       private feedback - but the number was wrong.)")
    print()

    print("=" * 78)
    print("V6  positive control for store detection")
    print("=" * 78)
    s = store234(v)
    print("      str.w ...,#0x234 sites: %s"
          % " ".join("0x%08x" % (LOAD + o) for o in s))
    check("V6.1 exactly one store to +0x234 exists (the patched line writes it once)",
          len(s) == 1)
    check("V6.2 it is the patched line, i.e. 0x%08x" % STORE234,
          s == [STORE234 - LOAD])
    print()

    print("=" * 78)
    print("V7  the emitted packages (if present)")
    print("=" * 78)
    for path, name in ((PKG, "variant A (mov+nop+nop)"),
                       (PKG_B, "variant B (1 byte)")):
        if not os.path.exists(path):
            print("  [skip] %s not generated yet: %s" % (name, path))
            continue
        raw = open(path, "rb").read()
        pl = raw[0x20:]
        md5 = hashlib.md5(pl).digest()
        hdr = raw[4:16] + raw[0x10:0x14]
        ln = struct.unpack_from("<I", raw, 0x14)[0]
        print("  --- %s ---" % name)
        print("      file %d B   MD5 %s" % (len(raw), hashlib.md5(raw).hexdigest()))
        check("V7.1 %s: header MD5 matches payload" % name, hdr == md5)
        check("V7.2 %s: length field matches payload" % name, ln == len(pl))
        check("V7.3 %s: magic/00000008/ffffffff intact" % name,
              raw[:4] == bytes.fromhex("d4c3b2a1")
              and raw[0x18:0x1C] == bytes.fromhex("00000008")
              and raw[0x1C:0x20] == bytes.fromhex("ffffffff"))
        check("V7.4 %s: payload size unchanged" % name, len(pl) == len(v))
        diffs = [k for k in range(len(v)) if v[k] != pl[k]]
        print("      payload bytes differing from source: %d  %s"
              % (len(diffs), " ".join("0x%x" % d for d in diffs)))
        check("V7.5 %s: changes confined to the patch site" % name,
              all(0x14AFE <= d <= 0x14B03 for d in diffs))
        dec = decode(pl[0x14AFE:0x14B04], LOAD + 0x14AFE, 6)
        print("      patched window decodes to: %s" % " ; ".join("%s %s" % t for t in dec))
        # variant A ends with the two NOPs, variant B ends with the move; both
        # must end the window with r1 = r0 as the last write to r1.
        check("V7.6 %s: the window's last write to r1 is `mov r1, r0`" % name,
              ("mov", "r1, r0") in dec
              and dec[dec.index(("mov", "r1, r0")):] ==
                  [("mov", "r1, r0")] + [("nop", "")] * (len(dec) - 1 - dec.index(("mov", "r1, r0"))))
        # This is the check that catches the `bf 00` trap: writing the NOP as
        # bf00 instead of 00bf decodes to `lsls r7,r7,#2`, i.e. a register write
        # that is not r1.  Assert no instruction in the window writes anything
        # other than r1 and nothing writes memory at all.
        md = make_md()
        md.detail = True
        bad = []
        for ins in md.disasm(pl[0x14AFE:0x14B04], LOAD + 0x14AFE):
            try:
                ops = ins.operands
            except Exception:
                continue
            for op in ops:
                if op.type == CS_OP_MEM and (op.access & 2):
                    bad.append("%s %s writes memory" % (ins.mnemonic, ins.op_str))
                if op.type == CS_OP_REG and (op.access & 2) \
                        and ins.reg_name(op.reg) != "r1":
                    bad.append("%s %s writes %s"
                               % (ins.mnemonic, ins.op_str, ins.reg_name(op.reg)))
        check("V7.8 %s: no instruction in the window writes any register but r1, "
              "and none writes memory" % name, not bad, "; ".join(bad))
        check("V7.7 %s: the store after the window is still at 0x%08x" % (name, STORE234),
              pl[0x14B04:0x14B08] == v[0x14B04:0x14B08])
    print()

    print("=" * 78)
    if FAIL:
        print("RESULT: %d CHECK(S) FAILED" % len(FAIL))
        for f in FAIL:
            print("   - %s" % f)
    else:
        print("RESULT: ALL CHECKS PASSED")
    print("=" * 78)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
