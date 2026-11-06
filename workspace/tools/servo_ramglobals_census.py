#!/usr/bin/env python3
"""Complete census of RAM addresses referenced from the literal pools, both builds.

WHY
  The patch target hinges on: "the 3150 position chain adds a term read from
  global 0x20003DB0+0x18 that D8 does not have".  D8 has 0 literal references
  to 0x20003DB0 - but 3150's companion struct is 0x20003D8C and
  0x20003D8C + 0x24 == 0x20003DB0, so the two globals are ADJACENT.  If D8's
  equivalent struct is 0x20003ED4 and D8 also references 0x20003ED4+0x24 =
  0x20003EF8, then D8 has the same subsystem and the "extra term" reading is
  wrong.  This tool settles it by enumerating every RAM address either build
  can name, with counts, side by side.

METHOD
  A sequential capstone sweep with skipdata (see servo_img.make_md): every
  instruction capstone can decode is inspected for a literal load, and the
  literal value is read from the real pool location Align(PC,4)+imm.  This
  respects Thumb-2 instruction boundaries, unlike a raw halfword scan.
  Both builds are processed identically, so the comparison is apples to apples.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from servo_img import make_md  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES = {
    "D8": os.path.join(ROOT, "data/servo_fw_samples/elf/v328d8.bin"),
    "3150": os.path.join(ROOT, "data/servo_fw_samples/elf/v3150.bin"),
}
LOAD = 0x08010000
LO, HI = 0x20000000, 0x20100000


def payload(p):
    d = open(p, "rb").read()
    if d[:4] == bytes.fromhex("d4c3b2a1"):
        d = d[0x20:]
    return d


def lit(pl, i, imm):
    a = ((i + 4) & ~3) + imm
    if a + 4 > len(pl):
        return None
    return struct.unpack_from("<I", pl, a)[0]


def sweep(pl):
    """Return {ram_addr: [site_offsets]} for literal loads naming RAM."""
    md = make_md()
    hits = {}
    n = 0
    for ins in md.disasm(pl, LOAD):
        n += 1
        m, op = ins.mnemonic, ins.op_str
        if not (m.startswith("ldr") and "[pc" in op):
            continue
        o = ins.address - LOAD
        # capstone prints `[pc, #0x1c]`  (skipdata suppresses the lit@ form)
        try:
            imm = int(op.split("#")[1].split("]")[0].strip(), 0)
        except Exception:
            continue
        v = lit(pl, o, imm)
        if v is None or not (LO <= v < HI):
            continue
        hits.setdefault(v, []).append(ins.address)
    return hits, n


def main():
    out = []
    P = out.append
    data = {}
    for name, path in IMAGES.items():
        pl = payload(path)
        h, n = sweep(pl)
        data[name] = h
        P("  %s : %d instructions decoded, %d distinct RAM literals, %d sites"
          % (name, n, len(h), sum(len(v) for v in h.values())))
    P("")

    keys = sorted(set(data["D8"]) | set(data["3150"]))
    P("=" * 78)
    P("ALL RAM LITERALS  (addr : D8 count | 3150 count)")
    P("=" * 78)
    only8 = [k for k in keys if k not in data["3150"]]
    only3 = [k for k in keys if k not in data["D8"]]
    both = [k for k in keys if k in data["D8"] and k in data["3150"]]
    P("  shared           : %d" % len(both))
    P("  D8 only          : %d" % len(only8))
    P("  the other only   : %d" % len(only3))
    P("")
    P("  -- the 0x20003c00..0x20004000 band, address by address --")
    for k in keys:
        if not (0x20003C00 <= k < 0x20004000):
            continue
        P("    0x%08x   D8=%-3d  3150=%-3d   %s"
          % (k, len(data["D8"].get(k, [])), len(data["3150"].get(k, [])),
             "both" if k in data["D8"] and k in data["3150"]
             else ("D8 ONLY" if k in data["D8"] else "3150 ONLY")))
    P("")
    P("  -- every D8-only RAM literal (any band) --")
    for k in only8:
        P("    0x%08x  %d site(s): %s"
          % (k, len(data["D8"][k]),
             " ".join("0x%08x" % a for a in data["D8"][k][:6])))
    P("")
    P("  -- every 3150-only RAM literal (any band) --")
    for k in only3:
        P("    0x%08x  %d site(s): %s"
          % (k, len(data["3150"][k]),
             " ".join("0x%08x" % a for a in data["3150"][k][:6])))
    P("")
    P("  -- shared literals whose USE COUNT differs a lot --")
    for k in both:
        a, b = len(data["D8"][k]), len(data["3150"][k])
        if max(a, b) >= 6 and abs(a - b) >= max(4, 0.5 * max(a, b)):
            P("    0x%08x  D8=%-3d 3150=%-3d" % (k, a, b))

    txt = "\n".join(out)
    dst = os.path.join(ROOT, "data/servo_fw_samples/RAM_GLOBALS_CENSUS.txt")
    with open(dst, "w", encoding="utf-8") as f:
        f.write(txt + "\n")
    print(txt.encode("ascii", "replace").decode("ascii"))
    print("\n[written] %s" % dst)


if __name__ == "__main__":
    main()
