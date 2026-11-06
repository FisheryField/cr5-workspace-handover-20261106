#!/usr/bin/env python3
"""zf_t1.py -- T1 "encoder preset / zeroing layer" helper.

Address convention: TRUE flash address = 0x08010000 + file offset (see z_fw.py).

Commands
  sc                        positive-control self check (both images)
  find97                    find `movs rD,#0x97` (encoder-init family stride)
  magic                     find persistence magics / flash target addresses
  sweep <tag>               build call + literal-pool caches (.zwork)
  callers <tag> <addr>      who BLs <addr>
  lit <tag> <value>         who loads dword <value> from the literal pool
  field <tag> <base> <o..>  for every pool load of <base>, dump window and flag offsets
  dis <tag> <addr> <n> [off..]   disassemble; flag lines matching offs
  diff <tagA> <aA> <tagB> <aB> <n>   side-by-side normalised comparison
  bounds <tag> <addr>       walk back to the enclosing push{...,lr}
"""
import sys, os, json, re, struct

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from z_fw import Fw, VERSION_FLASH

ROOT = os.path.dirname(HERE)
CACHE = os.path.join(ROOT, '.zwork')

POOL_RE = re.compile(r'\[pc, #(0x[0-9a-f]+)\]')


def fwt(t):
    return Fw(t)


def hx(a):
    return '%08x' % a


def listing(f, addr, n):
    return list(f.dis(addr, n))


def cmd_sc(args):
    for t in ('3150', 'd8'):
        f = fwt(t)
        print('== %s payload %d bytes  end %08x' % (t, len(f.code), f.end))
        print('   version string @ %s (want %s)' % (
            hx(f.base + f.code.find(b'DS.', f.off(VERSION_FLASH[t]) - 8)),
            hx(VERSION_FLASH[t])))
        for i in f.dis(0x0801019C, 2):
            print('   reset: %08x %-6s %s' % (i.address, i.mnemonic, i.op_str))


def cmd_find97(args):
    """Positive control: 3150 MUST report a hit at 0x08021742 (movs r0,#0x97)."""
    for t in ('3150', 'd8'):
        f = fwt(t)
        out = []
        for rd in range(8):
            pat = bytes([0x97, 0x20 | rd])
            i = f.code.find(pat)
            while i >= 0:
                out.append((f.base + i, rd))
                i = f.code.find(pat, i + 1)
        print('== %s  movs rD,#0x97 : %d hits' % (t, len(out)))
        for a, rd in sorted(out):
            print('   %08x  movs r%d,#0x97' % (a, rd))


def cmd_magic(args):
    magics = [('BE6D4A8B', 0xBE6D4A8B), ('A1B2C3D4', 0xA1B2C3D4),
              ('0800C000', 0x0800C000), ('08080000', 0x08080000)]
    for t in ('3150', 'd8'):
        f = fwt(t)
        for nm, v in magics:
            hits = f.find(struct.pack('<I', v))
            print('== %s %-9s : %2d  %s' % (t, nm, len(hits),
                                            ' '.join(hx(h) for h in hits[:24])))


def _sweep(t):
    p = os.path.join(CACHE, '%s_sweep.json' % t)
    if os.path.exists(p):
        d = json.load(open(p))
        return d
    f = fwt(t)
    calls, lit, pushes = {}, {}, []
    for i in f.md().disasm(f.code, f.base):
        ops = i.op_str
        if i.mnemonic in ('bl', 'blx'):
            try:
                tgt = int(ops.split('#')[-1], 0)
            except Exception:
                continue
            calls.setdefault(hx(tgt), []).append(hx(i.address))
        elif i.mnemonic.startswith('push') and 'lr' in ops:
            pushes.append(hx(i.address))
        m = POOL_RE.search(ops)
        if m:
            imm = int(m.group(1), 16)
            pool = ((i.address + 4) & ~3) + imm
            try:
                val = struct.unpack_from('<I', f.code, f.off(pool))[0]
            except Exception:
                continue
            lit.setdefault(hx(val), []).append([hx(i.address), hx(pool)])
    d = {'calls': calls, 'lit': lit, 'pushes': pushes}
    json.dump(d, open(p, 'w'))
    return d


def cmd_sweep(args):
    for t in args:
        d = _sweep(t)
        print('== %s sweep: %d call targets, %d literal values, %d pushes'
              % (t, len(d['calls']), len(d['lit']), len(d['pushes'])))


def cmd_callers(args):
    t, addr = args[0], int(args[1], 16)
    d = _sweep(t)
    src = d['calls'].get(hx(addr), [])
    print('== %s callers of %s : %d' % (t, hx(addr), len(src)))
    for s in src:
        print('   %s' % s)


def cmd_lit(args):
    t, val = args[0], int(args[1], 16)
    d = _sweep(t)
    src = d['lit'].get(hx(val), [])
    print('== %s literal loads of %s : %d' % (t, hx(val), len(src)))
    for s, p in src:
        print('   site %s  pool %s' % (s, p))


def _flag(i, offs):
    if not offs:
        return False
    for o in offs:
        if ('#0x%x]' % o) in i.op_str or ('#%d]' % o) in i.op_str:
            return True
    return False


def cmd_dis(args):
    t, addr, n = args[0], int(args[1], 16), int(args[2])
    offs = [int(x, 0) for x in args[3:]]
    f = fwt(t)
    for i in listing(f, addr, n):
        print('%s%08x  %-10s %s' % ('* ' if _flag(i, offs) else '  ',
                                    i.address, i.mnemonic, i.op_str))


def cmd_bounds(args):
    t, addr = args[0], int(args[1], 16)
    d = _sweep(t)
    cand = [int(p, 16) for p in d['pushes'] if int(p, 16) <= addr]
    print('== %s enclosing push{lR} before %s : %s' % (
        t, hx(addr), hx(max(cand)) if cand else 'none'))


def cmd_field(args):
    t, base = args[0], int(args[1], 16)
    offs = [int(x, 0) for x in args[2:]]
    d = _sweep(t)
    src = d['lit'].get(hx(base), [])
    print('== %s pool loads of base %s : %d sites' % (t, hx(base), len(src)))
    f = fwt(t)
    for s, p in src:
        a = int(s, 16)
        print('-- site %s (pool %s)  --' % (s, p))
        for i in listing(f, a, 60):
            if _flag(i, offs):
                print('   * %08x  %-10s %s' % (i.address, i.mnemonic, i.op_str))


def cmd_diff(args):
    ta, aa, tb, ab, n = args[0], int(args[1], 16), args[2], int(args[3], 16), int(args[4])
    fa, fb = fwt(ta), fwt(tb)
    la, lb = listing(fa, aa, n), listing(fb, ab, n)
    same = 0
    for k in range(max(len(la), len(lb))):
        x = la[k] if k < len(la) else None
        y = lb[k] if k < len(lb) else None
        sx = '%s %s' % (x.mnemonic, x.op_str) if x else ''
        sy = '%s %s' % (y.mnemonic, y.op_str) if y else ''
        if sx == sy:
            same += 1
        print('%3d | %-34s | %s' % (k, sx, sy))
    print('-- identical mnemonic+operands: %d/%d' % (same, max(len(la), len(lb))))


def cmd_ubfx43(args):
    """Encoder-type dispatch signature: ubfx rX,rY,#4,#3.
    Positive control: 3150 MUST include 0x0802175c."""
    for t in ('3150', 'd8'):
        f = fwt(t)
        hits = []
        for i in f.md().disasm(f.code, f.base):
            if i.mnemonic.startswith('ubfx') and '#4, #3' in i.op_str:
                hits.append((i.address, i.op_str))
        print('== %s ubfx ...,#4,#3 : %d hits' % (t, len(hits)))
        for a, o in hits[:40]:
            print('   %08x  %s' % (a, o))


def cmd_dpool(args):
    """Disassemble and resolve every pc-relative pool load to its dword."""
    t, addr, n = args[0], int(args[1], 16), int(args[2])
    f = fwt(t)
    for i in listing(f, addr, n):
        extra = ''
        m = POOL_RE.search(i.op_str)
        if m:
            pool = ((i.address + 4) & ~3) + int(m.group(1), 16)
            try:
                val = struct.unpack_from('<I', f.code, f.off(pool))[0]
                extra = '   ; pool %s = %s' % (hx(pool), hx(val))
            except Exception:
                pass
        print('  %08x  %-10s %-30s%s' % (i.address, i.mnemonic, i.op_str, extra))


def cmd_window(args):
    t, addr, nb, nf = args[0], int(args[1], 16), int(args[2]), int(args[3])
    f = fwt(t)
    print(cmd_window.__doc__ or '')
    print(f.text(addr - nb, nb + nf))


def cmd_bytes(args):
    t, pat = args[0], bytes.fromhex(args[1])
    f = fwt(t)
    hits = f.find(pat)
    print('== %s pattern %s : %d hits  %s' % (t, args[1], len(hits),
                                              ' '.join(hx(h) for h in hits[:30])))


def cmd_str(args):
    """ASCII strings matching a regex.  Positive control (must hit):
    'Position Actual Value' in both images."""
    t, pat = args[0], args[1]
    lim = int(args[2]) if len(args) > 2 else 60
    f = fwt(t)
    rx = re.compile(pat.encode())
    out = []
    for m in re.finditer(rb'[ -~]{4,}', f.code):
        if rx.search(m.group()):
            out.append((f.base + m.start(), m.group().decode('ascii', 'replace')))
    print('== %s strings /%s/ : %d hits' % (t, pat, len(out)))
    for a, s in out[:lim]:
        print('   %08x  %s' % (a, s[:100]))


def cmd_odwalk(args):
    """Walk the OD metadata table: name\\0 + u16 type + u16 bits + u16 attr."""
    t, addr, n = args[0], int(args[1], 16), int(args[2])
    f = fwt(t)
    a = addr
    for k in range(n):
        try:
            o = f.off(a)
        except Exception:
            break
        e = f.code.find(b'\x00', o)
        if e < 0:
            break
        name = f.code[o:e].decode('ascii', 'replace')
        ty, bits, attr = struct.unpack_from('<HHH', f.code, e + 1)
        print('%3d %08x  %-34s type=%04x bits=%d attr=%04x' % (k, a, name, ty, bits, attr))
        a = e + 7


CMDS = {'sc': cmd_sc, 'find97': cmd_find97, 'magic': cmd_magic, 'sweep': cmd_sweep,
        'callers': cmd_callers, 'lit': cmd_lit, 'field': cmd_field, 'dis': cmd_dis,
        'diff': cmd_diff, 'bounds': cmd_bounds, 'ubfx43': cmd_ubfx43,
        'dpool': cmd_dpool, 'window': cmd_window, 'bytes': cmd_bytes,
        'str': cmd_str, 'odwalk': cmd_odwalk}

if __name__ == '__main__':
    CMDS[sys.argv[1]](sys.argv[2:])
