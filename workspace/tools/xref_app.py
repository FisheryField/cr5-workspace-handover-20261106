"""xref_app.py - find code that references given runtime addresses inside the
Application.app runtime image, by disassembling the live memory dump.

The image is relocated at load time, so this works on the dump (the static file
still holds placeholders).  See APP_OFFSET_MAP.md.

usage:
  python tools\\xref_app.py --str "a1.config.write" "IoConfig_Globals"
  python tools\\xref_app.py --addr 0x75b5cf9c
  python tools\\xref_app.py --dump-strings
"""
import sys, os, gzip, re, struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUMP = os.path.join(BASE_DIR, "data", "appmap", "high_73000000.bin.gz")
DUMP_BASE = 0x73000000
IMG_LO, IMG_HI = 0x75a76000, 0x75cb8000     # the loaded Application image

M = None


def load():
    global M
    if M is None:
        M = gzip.open(DUMP, 'rb').read()
        print("# dump %s  %d bytes  base 0x%08x" %
              (os.path.basename(DUMP), len(M), DUMP_BASE))
    return M


def at(addr, n=64):
    o = addr - DUMP_BASE
    if o < 0 or o >= len(M):
        return b""
    return M[o:o + n]


def find_str(needle):
    """runtime addresses where `needle` occurs (ascii and utf16le)"""
    m = load()
    out = []
    for enc in (needle.encode('ascii'), needle.encode('utf-16-le')):
        i = m.find(enc)
        while i != -1:
            out.append(DUMP_BASE + i)
            i = m.find(enc, i + 1)
    return sorted(out)


def find_pointer(addr, limit=16):
    """dump offsets that hold a 32-bit pointer to addr"""
    m = load()
    w = struct.pack("<I", addr)
    out = []
    i = m.find(w)
    while i != -1 and len(out) < limit:
        out.append(DUMP_BASE + i)
        i = m.find(w, i + 1)
    return out


def refs(lo, hi, target):
    """scan Thumb code for references to target: ldr-from-literal-pool that
    resolves to target, or target used as an immediate/memory displacement"""
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.detail = True
    o = lo - DUMP_BASE
    code = M[o:o + (hi - lo)]
    hits = []
    for ins in md.disasm(code, lo):
        s = ins.op_str
        if "[pc" in s:
            mt = re.search(r'#(-?0x[0-9a-fA-F]+|-?\d+)', s)
            if mt:
                imm = int(mt.group(1), 0)
                lit = ((ins.address + 4) & ~3) + imm
                if (lit & 0xffffffff) == target:
                    hits.append(("ldr-lit", ins))
        for op in ins.operands:
            if op.type == 2 and (op.imm & 0xffffffff) == target:
                hits.append(("imm", ins))
                break
            if op.type == 3 and (op.mem.disp & 0xffffffff) == target:
                hits.append(("mem", ins))
                break
    return hits


def main(argv):
    load()
    if not argv:
        print(__doc__)
        return 2

    if argv[0] == "--dump-strings":
        pat = re.compile(b'[\x20-\x7e]{8,}')
        n = 0
        for mt in pat.finditer(M):
            a = DUMP_BASE + mt.start()
            if IMG_LO <= a < IMG_HI:
                print("0x%08x  %s" % (a, mt.group()[:110].decode('ascii')))
                n += 1
        print("# %d strings in the image extent" % n)
        return 0

    if argv[0] == "--str":
        targets = []
        for s in argv[1:]:
            a = find_str(s)
            print("# %-26r -> %s" % (s, " ".join("0x%08x" % x for x in a) or "NOT FOUND"))
            targets += a
    elif argv[0] == "--addr":
        targets = [int(x, 16) for x in argv[1:]]
    else:
        print(__doc__)
        return 2

    for t in targets:
        print()
        print("=== 0x%08x  %r" % (t, at(t, 48).split(b'\0')[0][:40]))
        p = find_pointer(t)
        if p:
            print("  pointer words: %s" % " ".join("0x%08x" % x for x in p))
        hits = refs(IMG_LO, IMG_HI, t)
        print("  code refs: %d" % len(hits))
        for kind, ins in hits[:24]:
            print("    %-8s 0x%08x  %-8s %s" % (kind, ins.address, ins.mnemonic, ins.op_str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
