#!/usr/bin/env python3
"""T5: enumerate every instruction that touches a per-axis descriptor FIELD
(+0x230 = 0x6062 Position demand value, +0x238 = 0x6064 Position actual value)
and, for each site, resolve as much of the addressing chain as the bytes allow.

WHY THIS SHAPE
  These fields live in the RAM descriptor array whose address is computed as
      descriptor_base + axis*0x329 + field
  (axis is dynamic), so tools that expect a *constant* base register return 0
  sites.  The raw instruction text `[rX, #0x230]` / `[rX, #0x238]` with a
  12-bit displacement IS observable though -- and it is the only thing visible
  statically.  So: sweep the whole image, collect those sites, then for each one
  disassemble the enclosing region and print the addressing chain.

ADDRESSING (project red line)
  * file offset + 0x08010000 == REAL flash address
  * Ghidra project coordinate + 0x10000 == real flash address
  Both `.elf` files are loaded here through their program headers, so the
  printed addresses are real flash addresses.

Positive control (printed before results, MUST pass):
  +0x238 write   D8 0x08015602 / 3150 0x08014B62
  +0x238 read    D8 0x08015344 / 3150 0x08014824
  +0x230 read    D8 0x08010E7E
  A tool that cannot see these is broken and its empty result means nothing.
"""
import struct
import sys
from collections import defaultdict

sys.path.insert(0, __file__.rsplit("\\", 1)[0])
from servo_img import make_md   # noqa: E402

LD = ('ldr', 'ldrh', 'ldrb', 'ldrsb', 'ldrsh', 'ldrd', 'vldr', 'vldrh', 'vldm')
ST = ('str', 'strh', 'strb', 'strd', 'vstr', 'vstrh', 'vstm')

CTRL = {
    'v328d8.elf': [('R', 0x238, 0x08015344), ('W', 0x238, 0x08015602),
                   ('R', 0x230, 0x08010E7E)],
    'v3150.elf':  [('R', 0x238, 0x08014824), ('W', 0x238, 0x08014B62),
                   ('R', 0x230, 0x08010E7E)],
}


def norm(mn):
    return mn[:-2] if mn.endswith('.w') else mn


DESC = '  (real flash addr = ELF addr + 0x10000)'


def load_elf(path):
    """Return (code, base, segs) for the .text section (vaddr 0x08000000).

    These ELFs are hand-built (tools/mkelf.py) with NO program headers, so the
    bytes must come from the section headers.  Address space = the project's
    Ghidra coordinate: real flash address = ELF address + 0x10000.
    """
    d = open(path, 'rb').read()
    assert d[:4] == b'\x7fELF', path
    assert d[4] == 1, 'not 32-bit'
    shoff, = struct.unpack_from('<I', d, 0x20)
    shentsize, shnum, shstrndx = struct.unpack_from('<HHH', d, 0x2E)
    shs = [struct.unpack_from('<IIIIIIIIII', d, shoff + k * shentsize)
           for k in range(shnum)]
    strtab = shs[shstrndx][4]
    segs = []
    for nm, typ, _fl, addr, off, size, *_ in shs:
        e = d.index(b'\x00', strtab + nm)
        name = d[strtab + nm:e].decode()
        if typ == 1 and size:                     # SHT_PROGBITS
            segs.append((name, addr, off, size))
    base = min(a for _n, a, _o, _s in segs)
    hi = max(a + s for _n, a, _o, s in segs)
    buf = bytearray(b'\x00' * (hi - base))
    for _n, a, o, s in segs:
        buf[a - base:a - base + s] = d[o:o + s]
    return bytes(buf), base, [(n, hex(a), hex(o), hex(s)) for n, a, o, s in segs]


def sweep(md, code, base, fields=(0x230, 0x238)):
    """Chunked linear pass (skipdata) -> all instructions + the touches we want.

    Chunked because capstone raises MemoryError on a whole-image disasm() of a
    ~350 KB stream.  Chunk boundaries are re-aligned to a decoded instruction:
    with skipdata on, capstone consumes an unknown byte as one .byte insn, so
    restarting at a chunk edge can resync to the wrong halfword -- we therefore
    back the next start off to the end of the last fully decoded instruction.
    """
    insns = []
    hits = defaultdict(list)
    a = base
    end = base + len(code)
    while a < end:
        chunk = code[a - base:min(end, a - base + 0x2000)]
        got = list(md.disasm(chunk, a))
        if not got:
            a += 2
            continue
        for i in got:
            if i.mnemonic == '.byte':
                continue
            insns.append(i)
            mn = norm(i.mnemonic)
            if mn in LD + ST and '[' in i.op_str:
                body = i.op_str[i.op_str.index('[') + 1:].split(']')[0]
                parts = [x.strip() for x in body.split(',')]
                if len(parts) == 2 and parts[1].startswith('#'):
                    try:
                        disp = int(parts[1][1:], 0)
                    except ValueError:
                        disp = -1
                    if disp in fields:
                        kind = 'W' if mn in ST else 'R'
                        hits[(kind, disp)].append((i.address, i.mnemonic, i.op_str,
                                                   parts[0], disp))
        a = got[-1].address + got[-1].size
    return insns, hits


def chain(insns, addr, reg, look=40):
    """Scan the `look` decoded instructions before addr for reg's last def,
    plus any 0x329 stride / descriptor-base literal anywhere in the window."""
    idx = None
    for k, i in enumerate(insns):
        if i.address >= addr:
            idx = k
            break
    if idx is None:
        return None, None, None
    prev = stride = desclit = None
    for i in insns[max(0, idx - look):idx]:
        ops = i.op_str
        first = ops.split(',')[0].strip() if ops else ''
        if first == reg:
            prev = (i.address, i.mnemonic, ops)
        if '0x329' in ops and stride is None:
            stride = (i.address, i.mnemonic, ops)
        for lit in ('0x2000138c', '0x2000129c'):
            if lit in ops and desclit is None:
                desclit = (i.address, i.mnemonic, ops)
    return prev, stride, desclit


def main(argv):
    images = argv if argv else [
        r'data\servo_fw_samples\elf\v328d8.elf',
        r'data\servo_fw_samples\elf\v3150.elf',
    ]
    md = make_md()
    fails = 0
    for path in images:
        code, base, segs = load_elf(path)
        name = path.replace('\\', '/').rsplit('/', 1)[-1]
        print('=' * 78)
        print('IMAGE %s   segs=%s' % (name, segs))
        print('ADDRESS SPACE: Ghidra coordinate (real flash = +0x10000)')
        print('=' * 78)
        hits = sweep(md, code, base)
        insns, hits = hits

        print('--- positive control ---')
        for kind, field, addr in CTRL.get(name, []):
            got = [h for h in hits[(kind, field)] if h[0] == addr]
            if not got:
                fails += 1
            print('  %s +0x%03X @ %08X : %s' %
                  (kind, field, addr,
                   ('PASS  ' + ' '.join(got[0][1:3])) if got else 'FAIL'))

        for field in (0x230, 0x238):
            for kind in ('W', 'R'):
                rows = sorted(hits[(kind, field)])
                print('\n--- %s +0x%03X : %d site(s) ---' %
                      ('WRITE' if kind == 'W' else 'READ ', field, len(rows)))
                for addr, mn, ops, reg, _d in rows:
                    prev, stride, dl = chain(insns, addr, reg)
                    print('  %08X  %-9s %-30s base=%s' % (addr, mn, ops, reg))
                    print('        base def : %s' %
                          ('%08X  %-9s %s' % prev if prev else '(none/arg/stack)'))
                    if stride:
                        print('        stride   : %08X  %-9s %s' % stride)
                    if dl:
                        print('        desc lit : %08X  %-9s %s' % dl)
        print()

    print('positive-control failures: %d' % fails)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
