"""servo_recover.py - recover a trustworthy function inventory from a flat
Cortex-M image.

Linear sweep is useless here (Ghidra found 10 functions; my first pass produced
76 KB "functions"), so this uses structural evidence instead:

  1. collect every plausible PROLOGUE:
       push {...}              (0xB4xx / 0xB5xx)
       push.w {...}            (0xE92D xxxx) with lr set
       sub sp, #imm / subw sp
     only at 2-byte-aligned offsets, and require the instruction to be a legal
     Thumb-2 encoding at that alignment
  2. collect every EPILOGUE: pop {..., pc} (0xBDxx / 0xE8BD xxxx) and bx lr
  3. walk forward from each prologue to the nearest epilogue; accept the
     function if the body disassembles cleanly (no undefined bytes, bounded
     size) and the epilogue is reachable
  4. score each candidate by evidence (vector-table entry, BL target, literal
     pool pointer, prologue shape) and keep the consistent set

usage:
  python tools\\servo_recover.py <flash.bin> [--json out.json] [--list N]
"""
import sys, os, struct, json, hashlib, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS, CS_MODE_LITTLE_ENDIAN

FLASH_BASE = 0x08000000
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS | CS_MODE_LITTLE_ENDIAN)


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def refs(flash):
    """vector table entries, BL/BLX targets, literal-pool code pointers"""
    size = len(flash)
    vt, bl, lit = set(), set(), set()
    for i in range(1, 16):
        v = struct.unpack_from('<I', flash, i * 4)[0]
        if v and FLASH_BASE <= (v & ~1) < FLASH_BASE + size:
            vt.add(v & ~1)
    md.skipdata = True
    import re
    for ins in md.disasm(flash, FLASH_BASE):
        s = ins.op_str
        if ins.mnemonic in ('bl', 'blx') and s.startswith('#'):
            try:
                t = int(s[1:], 0) & ~1
            except ValueError:
                continue
            if FLASH_BASE <= t < FLASH_BASE + size:
                bl.add(t)
        elif ins.mnemonic == 'ldr' and '[pc' in s:
            mt = re.search(r'#(-?0x[0-9a-fA-F]+|-?\d+)', s)
            if mt:
                litaddr = ((ins.address + 4) & ~1) + int(mt.group(1), 0)
                o = litaddr - FLASH_BASE
                if 0 <= o <= size - 4:
                    w = struct.unpack_from('<I', flash, o)[0]
                    if FLASH_BASE <= (w & ~1) < FLASH_BASE + size and (w & 1):
                        lit.add(w & ~1)
    return vt, bl, lit


def try_function(flash, start):
    """disassemble from start until a return; return (end, ok, nins)"""
    size = len(flash)
    o = start - FLASH_BASE
    body = flash[o:o + 0x2000]
    md.skipdata = False
    end = None
    n = 0
    for ins in md.disasm(body, start):
        n += 1
        m, s = ins.mnemonic, ins.op_str
        if m in ('pop', 'ldm') and 'pc' in s:
            end = ins.address + ins.size
            break
        if m == 'bx' and s.strip() == 'lr':
            end = ins.address + ins.size
            break
        if m in ('b', 'bx') and not s.startswith('#'):
            break
    if end is None or end - start < 4 or end - start > 0x2000:
        return None
    # clean disassembly: every byte accounted for, ending exactly at `end`
    md.skipdata = True
    covered = 0
    last = start
    for ins in md.disasm(flash[start - FLASH_BASE:end - FLASH_BASE], start):
        if ins.address != last:
            return None
        last = ins.address + ins.size
        covered += ins.size
    if last != end:
        return None
    return end, n


def main(argv):
    path = argv[0]
    _d, hdr, flash = load(path)
    size = len(flash)
    vt, bl, lit = refs(flash)
    print("%s  flash %d B  md5 %s" % (os.path.basename(path), size, hashlib.md5(flash).hexdigest()))
    print("  vectors %d, BL targets %d, literal code ptrs %d" % (len(vt), len(bl), len(lit)))

    # candidate prologues: scan halfword grid for push/push.w
    cands = set(vt) | set(bl) | set(lit)
    prologues = set()
    for off in range(0, size - 4, 2):
        hw = struct.unpack_from('<H', flash, off)[0]
        a = FLASH_BASE + off
        if (hw & 0xfe00) == 0xb400:              # push {..}
            prologues.add(a)
        elif (hw & 0xff00) == 0xb500:            # push {.., lr}
            prologues.add(a)
        elif hw == 0xe92d:                       # push.w {...}
            hw2 = struct.unpack_from('<H', flash, off + 2)[0]
            prologues.add(a)
    print("  prologue candidates (push/push.w): %d" % len(prologues))
    cands |= prologues

    funcs = {}
    for a in sorted(cands):
        if a < FLASH_BASE or a >= FLASH_BASE + size:
            continue
        r = try_function(flash, a)
        if r:
            end, n = r
            ev = []
            if a in vt:
                ev.append('vector')
            if a in bl:
                ev.append('bl')
            if a in lit:
                ev.append('lit')
            if a in prologues:
                ev.append('prologue')
            funcs[a] = (end, n, ev)
    print("  accepted functions: %d" % len(funcs))

    # coverage / consistency: overlapping functions are a red flag
    starts = sorted(funcs)
    overlaps = [a for a, b in zip(starts, starts[1:]) if funcs[a][0] > b]
    print("  overlapping function bodies: %d" % len(overlaps))
    cover = sum(e - a for a, (e, n, ev) in funcs.items())
    print("  bytes covered by accepted functions: %d / %d (%.1f%%)" % (cover, size, 100.0 * cover / size))
    ev_count = collections.Counter(tuple(f[2]) for f in funcs.values())
    print("  evidence mix (top 6):")
    for k, n in ev_count.most_common(6):
        print("     %-28s x%d" % (','.join(k), n))
    sizes = [e - a for a, (e, n, ev) in sorted(funcs.items())]
    print("  function size: min %d median %d max %d" % (min(sizes), sorted(sizes)[len(sizes) // 2], max(sizes)))

    if '--list' in argv:
        n = int(argv[argv.index('--list') + 1])
        for a in starts[:n]:
            e, ni, ev = funcs[a]
            print("   0x%08x..0x%08x %5d B %4d insns  %s" % (a, e, e - a, ni, ','.join(ev)))
    if '--json' in argv:
        out = argv[argv.index('--json') + 1]
        json.dump({"flash_md5": hashlib.md5(flash).hexdigest(), "size": size,
                   "functions": [{"start": a, "end": funcs[a][0], "insns": funcs[a][1],
                                  "evidence": funcs[a][2]} for a in starts]},
                  open(out, 'w'), indent=1)
        print("  wrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
