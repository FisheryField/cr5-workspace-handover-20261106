"""servo_fdif.py - function-level diff between two servo firmware builds.

Ghidra's auto analysis finds almost nothing on a flat Cortex-M image, so the
function inventory is built with capstone (see servo_funcs.py), then the two
inventories are matched:

  1. exact byte match of the whole function body
  2. else match by exact match of a normalised instruction "shape" (mnemonic +
     operand arity, branch targets masked) so that a function which only moved
     in flash is still recognised
  3. what is left over is genuinely new/changed code

usage: python tools\\servo_fdif.py <new.bin> <old.bin> [--top N] [--show-addr HEX]
"""
import sys, os, struct, json, hashlib, collections, re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS, CS_MODE_LITTLE_ENDIAN

FLASH_BASE = 0x08000000
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS | CS_MODE_LITTLE_ENDIAN)
md.detail = True


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def scan(flash):
    size = len(flash)
    starts = set()
    for i in range(1, 16):
        v = struct.unpack_from('<I', flash, i * 4)[0]
        if v and FLASH_BASE <= (v & ~1) < FLASH_BASE + size:
            starts.add(v & ~1)
    md.skipdata = True
    for ins in md.disasm(flash, FLASH_BASE):
        s = ins.op_str
        if ins.mnemonic in ('bl', 'blx') and s.startswith('#'):
            try:
                t = int(s[1:], 0) & ~1
            except ValueError:
                continue
            if FLASH_BASE <= t < FLASH_BASE + size:
                starts.add(t)
        elif ins.mnemonic == 'ldr' and '[pc' in s:
            mt = re.search(r'#(-?0x[0-9a-fA-F]+|-?\d+)', s)
            if mt:
                lit = ((ins.address + 4) & ~1) + int(mt.group(1), 0)
                off = lit - FLASH_BASE
                if 0 <= off <= size - 4:
                    w = struct.unpack_from('<I', flash, off)[0]
                    if FLASH_BASE <= (w & ~1) < FLASH_BASE + size and (w & 1):
                        starts.add(w & ~1)
    starts.add(struct.unpack_from('<I', flash, 4)[0] & ~1)
    return sorted(s for s in starts if FLASH_BASE <= s < FLASH_BASE + size)


def bodies(flash, starts):
    """[(start, end, bytes, shape)] where shape is a mnemonic+arity signature"""
    out = []
    md.skipdata = True
    for i, a in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else FLASH_BASE + len(flash)
        b = flash[a - FLASH_BASE:end - FLASH_BASE]
        if len(b) > 0x4000:
            b = b[:0x4000]
        shape = []
        for ins in md.disasm(b, a):
            op = ins.op_str
            # mask branch targets and pc-relative literals: they move when the
            # function is relocated
            op = re.sub(r'#-?0x[0-9a-fA-F]+', '#I', op)
            op = re.sub(r'#-?\d+', '#I', op)
            shape.append(ins.mnemonic + ' ' + op)
        out.append((a, end, b, tuple(shape)))
    return out


def main(argv):
    new_p, old_p = argv[0], argv[1]
    top = int(argv[argv.index('--top') + 1]) if '--top' in argv else 30
    _dn, _bn, fn = load(new_p)
    _do, _bo, fo = load(old_p)
    sn, so = scan(fn), scan(fo)
    bn, bo = bodies(fn, sn), bodies(fo, so)
    print("new %s: %d functions, %d B" % (os.path.basename(new_p), len(bn), len(fn)))
    print("old %s: %d functions, %d B" % (os.path.basename(old_p), len(bo), len(fo)))

    # index old by bytes and by shape
    by_bytes = {}
    for a, e, b, sh in bo:
        by_bytes.setdefault(hashlib.md5(b).hexdigest(), []).append(a)
    by_shape = collections.defaultdict(list)
    for a, e, b, sh in bo:
        by_shape[hash(sh)].append(a)

    exact = shape_only = newonly = 0
    new_funcs = []
    for a, e, b, sh in bn:
        h = hashlib.md5(b).hexdigest()
        if h in by_bytes:
            exact += 1
            continue
        if hash(sh) in by_shape:
            shape_only += 1
            continue
        newonly += 1
        new_funcs.append((a, e, b, sh))

    print()
    print("exact byte-identical functions : %d / %d (%.1f%%)" % (exact, len(bn), 100.0 * exact / len(bn)))
    print("same shape, different bytes     : %d  (moved/renumbered)" % shape_only)
    print("no match in the other build     : %d  <-- changed or new code" % newonly)
    print()
    print("=== the %d unmatched functions (largest first) ===" % len(new_funcs))
    for a, e, b, sh in sorted(new_funcs, key=lambda t: t[0] - t[1])[:top]:
        print("  0x%08x..0x%08x  %5d B   %d insns" % (a, e, e - a, len(sh)))
    if '--show-addr' in argv:
        addr = int(argv[argv.index('--show-addr') + 1], 16)
        for a, e, b, sh in bn:
            if a <= addr < e:
                print()
                print("=== disassembly of the function containing 0x%08x ===" % addr)
                md.skipdata = False
                for ins in md.disasm(fn[a - FLASH_BASE:e - FLASH_BASE], a):
                    print("  0x%08x  %-31s %-8s %s" %
                          (ins.address, fn[ins.address - FLASH_BASE:ins.address - FLASH_BASE + ins.size].hex(' '),
                           ins.mnemonic, ins.op_str))
                break
    json.dump({"new": os.path.basename(new_p), "old": os.path.basename(old_p),
               "new_funcs": len(bn), "exact": exact, "shape_only": shape_only,
               "unmatched": [{"addr": a, "end": e, "size": e - a} for a, e, b, sh in new_funcs]},
              open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                                'data', 'servo_fw_samples', 'func_diff.json'), 'w'), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
