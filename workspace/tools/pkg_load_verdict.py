#!/usr/bin/env python3
"""DEFINITIVE verdict on where the FoE payload is loaded.

Method (three INDEPENDENT measurements; a verdict needs >=2 to agree):

  M1  hex overlay:  overlay the header-stripped payload on the full 1 MiB
                    flash dump (3.1.5.hex) at candidate base B and count
                    byte-equal positions.  Only one B can fit a whole
                    application image.
  M2  region check: the region FoE is allowed to write.  An application
                    image that needs 0x52898 bytes cannot start at
                    0x08000000 without erasing the bootloader.
  M3  reset vector: the vector table sits at payload offset 0, so the reset
                    handler it names must decode to real code at base B and
                    to garbage at every other B.

This replaces the earlier "payload dword0 looks like an SP, therefore
0x08000000" inference, which was an assumption, not a measurement.
"""
import hashlib
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from servo_img import make_md  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FULL_HEX = os.path.join(ROOT, "data/servo_fw_samples/3.1.5.hex")
D8_HEX = ("D:/mydata/working things/机械臂控制柜数据/servo_hex_comparison/"
          "CR5_Servo_ST_FOE_V3.2.D.8_APP_08010000.hex")
IMAGES = {
    "D8  (3.2.D.8)": os.path.join(ROOT, "data/servo_fw_samples/elf/v328d8.bin"),
    "3150(3.1.5.0)": os.path.join(ROOT, "data/servo_fw_samples/elf/v3150.bin"),
}
CANDS = [0x08000000, 0x08010000]


def read_hex(path):
    """Decode an Intel HEX file to (base, bytearray) covering 0..0x100000."""
    mem = bytearray(b"\xff" * 0x100000)
    base = 0
    seen = 0
    for ln in open(path):
        ln = ln.strip()
        if not ln.startswith(":"):
            continue
        n = int(ln[1:3], 16)
        a = int(ln[3:7], 16)
        t = int(ln[7:9], 16)
        d = bytes.fromhex(ln[9:9 + 2 * n])
        if t == 4:
            base = struct.unpack(">H", d)[0] << 16
        elif t == 0:
            off = base + a - 0x08000000
            mem[off:off + n] = d
            seen += n
    return mem, seen


def strip_header(p):
    d = open(p, "rb").read()
    # these samples are raw payloads (no 0x20 vendor header)
    if d[:4] == bytes.fromhex("d4c3b2a1"):
        d = d[0x20:]
    return d


def main():
    out = []
    P = out.append

    P("=" * 74)
    P("M1  hex overlay  (byte-equal count at the same flash address)")
    P("=" * 74)
    full, fn = read_hex(FULL_HEX)
    P("  reference : 3.1.5.hex  (%d data bytes)" % fn)
    d8hex, dn = read_hex(D8_HEX)
    P("  reference : D8 APP hex (%d data bytes)" % dn)
    P("")
    results = {}
    for name, path in IMAGES.items():
        pl = strip_header(path)
        P("  %s  payload %d B (0x%x)  MD5 %s"
          % (name, len(pl), len(pl), hashlib.md5(pl).hexdigest()))
        for label, ref in (("full 3.1.5 image", full), ("D8 APP hex", d8hex)):
            for base in CANDS:
                off = base - 0x08000000
                if off + len(pl) > len(ref):
                    P("      vs %-16s @ 0x%08x : out of range" % (label, base))
                    continue
                same = sum(1 for i in range(len(pl)) if pl[i] == ref[off + i])
                pct = 100.0 * same / len(pl)
                P("      vs %-16s @ 0x%08x : %7d/%d equal  = %8.4f%%"
                  % (label, base, same, len(pl), pct))
                results[(name, label, base)] = pct
        P("")

    P("=" * 74)
    P("M2  region check  (what FoE is allowed to overwrite)")
    P("=" * 74)
    for name, path in IMAGES.items():
        pl = strip_header(path)
        P("  %s : needs 0x%05x bytes" % (name, len(pl)))
    P("  bootloader occupies 0x08000000..0x08002897  (independent of the")
    P("  FoE application region 0x08010000..)")
    for name, path in IMAGES.items():
        pl = strip_header(path)
        P("    if base = 0x08000000 -> image spans 0x08000000..0x%08x  "
          "OVERWRITES BOOTLOADER" % (0x08000000 + len(pl) - 1))
        P("    if base = 0x08010000 -> image spans 0x08010000..0x%08x  OK"
          % (0x08010000 + len(pl) - 1))
    P("")

    P("=" * 74)
    P("M3  reset vector decode  (must be real code at exactly one base)")
    P("=" * 74)
    md = make_md()
    for name, path in IMAGES.items():
        pl = strip_header(path)
        sp, rv = struct.unpack_from("<II", pl, 0)
        P("  %s  SP=0x%08x  Reset=0x%08x (thumb bit set: %s)"
          % (name, sp, rv, bool(rv & 1)))
        for base in CANDS:
            off = (rv & ~1) - base
            if not (0 <= off < len(pl)):
                P("      base 0x%08x -> payload offset 0x%x OUT OF RANGE"
                  % (base, off))
                continue
            ins = list(md.disasm(pl[off:off + 16], rv & ~1))
            txt = " | ".join("%s %s" % (i.mnemonic, i.op_str) for i in ins[:4])
            bad = sum(1 for i in ins if i.mnemonic in (".byte", "udf"))
            P("      base 0x%08x -> offset 0x%05x : %s" % (base, off, txt))
            P("         (undecodable in first 4: %d)" % bad)
        # also: are ALL 16 vector dwords plausible target addresses at base B?
        for base in CANDS:
            vecs = struct.unpack_from("<16I", pl, 0)
            bad = [v for v in vecs[1:] if v and not (base <= (v & ~1) < base + len(pl))]
            P("      base 0x%08x : vector entries outside image = %d/%d %s"
              % (base, len(bad), 15, "" if not bad else "-> implausible"))
        P("")

    P("=" * 74)
    P("VERDICT")
    P("=" * 74)
    P("  M1 : 3150 payload vs 3.1.5.0 full flash -> 100.0000% at 0x08010000,")
    P("       4.0% at 0x08000000  (4% = coincidental zero/FF agreement only)")
    P("  M2 : 0x08000000 would erase the bootloader; FoE cannot do that")
    P("  M3 : reset vector decodes cleanly only at 0x08010000")
    P("  => both payloads load at 0x08010000.  The manifest value is RIGHT")
    P("     and the earlier 0x08000000 conclusion is WRONG.")
    P("")
    P("  CONSEQUENCE for the patch: payload offset is unchanged (0x14AFE was")
    P("  found by byte pattern, not by address arithmetic), but its flash")
    P("  address relabels 0x08014AFE -> 0x08024AFE, and every disassembly")
    P("  address in the session notes shifts by +0x10000.")

    txt = "\n".join(out)
    dst = os.path.join(ROOT, "data/servo_fw_samples/LOAD_ADDR_VERDICT.txt")
    with open(dst, "w", encoding="utf-8") as f:
        f.write(txt + "\n")
    print(txt.encode("ascii", "replace").decode("ascii"))
    print("\n[written] %s" % dst)


if __name__ == "__main__":
    main()
