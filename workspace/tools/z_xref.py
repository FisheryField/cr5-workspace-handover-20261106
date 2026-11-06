#!/usr/bin/env python3
"""z_xref.py -- literal-pool cross-reference database for the two servo images.

Model (matches what the firmware actually does -- it does NOT use movw/movt for
32-bit addresses):
    a RAM global is materialised as   ldr rX,[pc,#n]   ->  dword in a literal pool
so the question "who touches RAM address A" becomes
    (1) find the pool dword equal to A         -> pool_addr
    (2) find every ldr/vldr whose target == pool_addr -> site list
and the question "who CALLS function F" becomes a scan for bl/blx #F.

Addresses printed are TRUE flash addresses (0x08010000 + file offset).

usage:
  python tools\\z_xref.py build <tag>
  python tools\\z_xref.py ram <tag> 0x20007400 [more...]
  python tools\\z_xref.py callers <tag> 0x08022390
  python tools\\z_xref.py func <tag> 0x08022390     -- literal set of one function
"""
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from z_fw import Fw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, '.zwork')

LOADS = ('ldr', 'ldrh', 'ldrb', 'ldrsb', 'ldrsh', 'ldrd', 'vldr')


def build(tag):
    f = Fw(tag)
    md = f.md()
    lits = {}       # pool_addr -> value (only dword-aligned, only if referenced)
    sites = {}      # pool_addr -> [(insn_addr, mnemonic)]
    calls = {}      # target -> [insn_addr]
    addr2idx = {}
    allins = []
    for i in md.disasm(f.code, f.base):
        allins.append(i)
    print('  instructions swept: %d' % len(allins))
    for i in allins:
        if i.mnemonic in ('bl', 'blx') and i.op_str.startswith('#'):
            try:
                t = int(i.op_str[1:], 0) & ~1
            except ValueError:
                continue
            if f.base <= t < f.end:
                calls.setdefault(t, []).append(i.address)
        if i.mnemonic not in LOADS or 'pc' not in i.op_str or '#' not in i.op_str:
            continue
        try:
            imm = int(i.op_str.split('#')[-1].rstrip(']'), 0)
        except ValueError:
            continue
        tgt = ((i.address + 4) & ~3) + imm
        if not (f.base <= tgt <= f.end - 4):
            continue
        sites.setdefault(tgt, []).append((i.address, i.mnemonic))
        if tgt % 4 == 0:
            lits[tgt] = struct.unpack_from('<I', f.code, tgt - f.base)[0]
    db = {
        'lits': {str(k): v for k, v in lits.items()},
        'sites': {str(k): v for k, v in sites.items()},
        'calls': {str(k): v for k, v in calls.items()},
    }
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, '%s_xref.json' % tag)
    json.dump(db, open(p, 'w'))
    print('  literal dwords referenced: %d ; bl targets: %d -> %s' % (len(lits), len(calls), p))
    # ---- positive controls -------------------------------------------------
    rev = {}
    for pa, v in lits.items():
        rev.setdefault(v, []).append(pa)
    print('  CONTROL 0x20007400 -> pool %s' % [hex(x) for x in rev.get(0x20007400, [])])
    tt = [i.address for i in allins if i.mnemonic == 'movw' and '0x4e20' in i.op_str]
    print('  CONTROL movw #0x4e20 -> %s' % [hex(x) for x in tt])
    return db


def load(tag):
    p = os.path.join(CACHE, '%s_xref.json' % tag)
    if not os.path.exists(p):
        return build(tag)
    d = json.load(open(p))
    return {
        'lits': {int(k): v for k, v in d['lits'].items()},
        'sites': {int(k): [tuple(x) for x in v] for k, v in d['sites'].items()},
        'calls': {int(k): v for k, v in d['calls'].items()},
    }


def rev_map(db):
    r = {}
    for pa, v in db['lits'].items():
        r.setdefault(v, []).append(pa)
    return r


def main(argv):
    cmd, tag = argv[0], argv[1]
    db = build(tag) if cmd == 'build' else load(tag)
    if cmd in ('build',):
        return 0
    if cmd == 'ram':
        r = rev_map(db)
        for s in argv[2:]:
            a = int(s, 0)
            pools = r.get(a, [])
            print('== %s  RAM 0x%08x  pool dwords: %s' % (tag, a, [hex(p) for p in pools]))
            for p in pools:
                for site, mn in db['sites'].get(p, []):
                    print('     load site 0x%08x  %s  <- pool 0x%08x' % (site, mn, p))
    elif cmd == 'callers':
        a = int(argv[2], 0)
        st = db['calls'].get(a, [])
        print('== %s  callers of 0x%08x : %d' % (tag, a, len(st)))
        for s in st[:60]:
            print('     0x%08x' % s)
    elif cmd == 'range':
        lo, hi = int(argv[2], 0), int(argv[3], 0)
        f = Fw(tag)
        n = 0
        for i in f.dis(lo, 4000):
            if i.address > hi:
                break
            print('  0x%08x  %-14s %s' % (i.address, i.bytes.hex(), i.mnemonic + ' ' + i.op_str))
            n += 1
            if n > 400:
                break
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
