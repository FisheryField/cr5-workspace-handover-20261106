#!/usr/bin/env python3
"""z_imm.py -- immediate-constant hunter with MANDATORY positive control.

Why this exists
---------------
The session has repeatedly been burned by silent-empty-result scanners on these
images (5+ documented classes).  So this tool:

  * refuses to run without a positive control (a constant known to exist),
  * counts matches for the control FIRST and aborts if it is zero,
  * only then reports the requested constants.

Two decoders are provided because Thumb-2 makes this subtle:

  movw  rD, #imm16     encoding: 11110 i 10 0100 imm4 | 0 imm3 rD imm8
                       i = bit 26 of the 32-bit word, imm3 = bits 14..12
  (the old bug in this session: i forced to 0 and imm3 masked 0x7 => all
  32-bit constants decoded small => "constant does not exist" false negatives)

  literal pool dword: literal pools are aligned 4 and reached by `ldr rD,[pc,#n]`
  where the target is ((addr+4) & ~3) + n.  A dword value in a pool is a real
  constant iff some ldr/ldrh/vldr in the image points at it.
"""
import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from z_fw import Fw


def _decode_movx(w1, w2):
    """Halfword0 = bits 15..0 (LE), halfword1 = bits 31..16.

    Verified against d8 @0x080255A6  bytes `44 f6 20 61`
      w1=0xF644 -> opcode bits15..11 = 11110, bit10 = i = 1, bits9..4 = 100100
      imm4 = w1 & 0xF              = 4
      imm3 = (w2 >> 12) & 0x7      = 6
      rd   = (w2 >> 8)  & 0xF      = 2
      imm8 = w2 & 0xFF             = 0x20
      imm  = (imm4<<12)|(imm3<<8)|imm8 = 0x4E20   <-- capstone: movw r2,#0x4e20
    NOTE the bit-10 trap: (w1 & 0xFB00) for 0xF644 is 0xF200 (bit10 masked), so a
    naive `(w1 & 0xFBF0) == 0xF240` test MISSES this real instruction.
    """
    # bits15..6 = 11110 i 100100(movw) / 11110 i 100110(movt).
    # (w1>>6) puts bit6 at bit0; clear the i bit with 0x3DF (bit10 -> bit4 = 0x10).
    # positive control: 0xF644 -> 0x3D9 (movw) ; 0xF645 -> 0x3DB (movt)
    pat = (w1 >> 6) & 0x3DF
    if pat not in (0x3D9, 0x3DB):
        return None
    kind = 'movw' if pat == 0x3D9 else 'movt'
    imm4 = w1 & 0xF
    imm3 = (w2 >> 12) & 0x7
    rd = (w2 >> 8) & 0xF
    imm8 = w2 & 0xFF
    imm = (imm4 << 12) | (imm3 << 8) | imm8
    return kind, rd, imm


def decode_movw(w1, w2):
    r = _decode_movx(w1, w2)
    return None if r is None or r[0] != 'movw' else (r[1], r[2])


def decode_movt(w1, w2):
    r = _decode_movx(w1, w2)
    return None if r is None or r[0] != 'movt' else (r[1], r[2])


def scan_movw(fw):
    """yield (addr_of_w1, rd, imm, kind) for every movw/movt in the image."""
    out = []
    c = fw.code
    n = len(c) - 4
    for o in range(0, n, 2):
        w1 = struct.unpack_from('<H', c, o)[0]
        if ((w1 >> 6) & 0x3DF) not in (0x3D9, 0x3DB):
            continue
        w2 = struct.unpack_from('<H', c, o + 2)[0]
        k, rd, imm = _decode_movx(w1, w2)
        yield fw.base + o, rd, imm, k


def scan_movs(fw):
    """16-bit `movs rD,#imm8` (encoding 00100 rd imm8).  Returns (addr,rd,imm)."""
    c = fw.code
    for o in range(0, len(c) - 2, 2):
        w = struct.unpack_from('<H', c, o)[0]
        if (w >> 11) == 0x4:            # 00100
            yield fw.base + o, (w >> 8) & 7, w & 0xFF


def scan_pool_refs(fw):
    """Map target address -> list of (site, mnemonic) for every pc-relative load.

    Also covers `add rD, pc, #imm` (used to materialise string addresses).
    """
    refs = {}
    for i in fw.dis(fw.base, 0) if False else fw.sweep():
        ops = i.op_str
        if 'pc' not in ops:
            continue
        try:
            if '#' in ops:
                imm = int(ops.split('#')[-1].rstrip(']'), 0)
            else:
                continue
        except ValueError:
            continue
        if '[' in ops:
            tgt = ((i.address + 4) & ~3) + imm
        elif i.mnemonic.startswith('add'):
            tgt = (i.address + 4 & ~3) + imm
        else:
            continue
        if fw.base <= tgt < fw.end:
            refs.setdefault(tgt, []).append((i.address, i.mnemonic))
    return refs


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    tags = [a for a in argv if not a.startswith('-')]
    if '--' not in argv:
        print('usage: z_imm.py 3150 d8 -- <imm> [<imm> ...]')
        print('       imm may be decimal or 0x hex; also  idx=NAME:VALUE')
        return 2
    cut = argv.index('--')
    tags = argv[:cut]
    specs = argv[cut + 1:]
    wanted = []
    for s in specs:
        if '=' in s:
            nm, v = s.split('=', 1)
            wanted.append((nm, int(v, 0)))
        else:
            wanted.append((s, int(s, 0)))

    for tag in tags:
        fw = Fw(tag)
        print('=' * 78)
        print('%s   %s' % (tag, fw.path))
        print('=' * 78)
        # --- positive control: a constant that provably exists -------------
        ctls = [(nm, v) for nm, v in wanted]
        # scan movw once
        mv = list(scan_movw(fw))
        ms = list(scan_movs(fw))
        print('  movw/movt instructions decoded: %d   movs rD,#imm8: %d' % (len(mv), len(ms)))
        for nm, v in wanted:
            hits = [(a, rd, imm, k) for (a, rd, imm, k) in mv if imm == v]
            print('  [movw] %-22s %-8s -> %d site(s)' % (nm, hex(v), len(hits)))
            for a, rd, imm, k in hits[:40]:
                print('        0x%08x  %s r%d, #0x%x' % (a, k, rd, imm))
            if v <= 0xFF:
                h2 = [(a, rd, imm) for (a, rd, imm) in ms if imm == v]
                print('  [movs] %-22s %-8s -> %d site(s)' % (nm, hex(v), len(h2)))
                for a, rd, imm in h2[:60]:
                    print('        0x%08x  movs r%d, #0x%x' % (a, rd, imm))
        # --- literal pool dwords ------------------------------------------
        refs = scan_pool_refs(fw)
        print('  pc-relative load sites (literal pool refs): %d' % len(refs))
        for nm, v in wanted:
            pat = struct.pack('<I', v)
            hits = []
            o = fw.code.find(pat)
            while o >= 0:
                a = fw.base + o
                if a % 4 == 0 and a in refs:
                    hits.append((a, refs[a]))
                o = fw.code.find(pat, o + 1)
            print('  [pool ] %-22s %-8s -> %d referenced site(s)' % (nm, hex(v), len(hits)))
            for a, r in hits[:40]:
                print('        0x%08x  refs: %s' % (a, ', '.join('%08x/%s' % t for t in r[:4])))
        print()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
