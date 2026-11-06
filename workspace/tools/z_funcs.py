#!/usr/bin/env python3
"""z_funcs.py -- function index + RAM-global cross-reference database for the
two servo images, built with capstone (addresses verified against the raw file).

Two documented traps this tool is built to avoid:
  * capstone needs skipdata or a whole-image sweep silently stops after ~1 KB
  * literal pools must be resolved as ((addr+4) & ~3) + imm  (Thumb PC alignment)

usage:
  python tools\\z_funcs.py build <tag>            -- write .zwork/<tag>_funcs.json
  python tools\\z_funcs.py who <tag> <hexaddr>     -- which functions touch that addr
  python tools\\z_funcs.py callers <tag> <hexaddr> -- which functions call that addr
  python tools\\z_funcs.py list <tag> <count>
  python tools\\z_funcs.py dis <tag> <hexaddr> <n>
  python tools\\z_funcs.py dd <tag> <hexaddr>      -- decompile-ish: raw asm listing w/ literals resolved
"""
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from z_fw import Fw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, '.zwork')
BRANCH = ('b', 'bl', 'bx', 'blx', 'cbz', 'cbnz', 'beq', 'bne', 'bgt', 'blt', 'bge',
          'ble', 'bhi', 'bls', 'bhs', 'blo', 'bcs', 'bcc', 'bmi', 'bpl', 'bvc', 'bvs')
LOAD = ('ldr', 'ldrh', 'ldrb', 'ldrsb', 'ldrsh', 'ldrd', 'vldr', 'ldm', 'ldmia',
        'ldmdb', 'pop')
STORE = ('str', 'strh', 'strb', 'strd', 'vstr', 'stm', 'stmia', 'stmdb', 'push')


def lit_addr(i):
    """If insn is a pc-relative load/store, return its target address."""
    ops = i.op_str
    if 'pc' not in ops or '#' not in ops:
        return None
    try:
        imm = int(ops.split('#')[-1].rstrip(']'), 0)
    except ValueError:
        return None
    return ((i.address + 4) & ~3) + imm


def build(tag):
    f = Fw(tag)
    md = f.md()
    funcs = {}          # entry -> {insns:[...], ram:set, calls:set, lits:dict}
    cur = None
    addrs = []
    for i in md.disasm(f.code, f.base):
        addrs.append(i)
    # function entries: every BL/BLX target inside the image, plus reset vector
    entries = set()
    rv = f.rd32(f.base + 4) & ~1
    entries.add(rv)
    for i in addrs:
        if i.mnemonic in ('bl', 'blx') and i.op_str.startswith('#'):
            try:
                t = int(i.op_str[1:], 0) & ~1
            except ValueError:
                continue
            if f.base <= t < f.end:
                entries.add(t)
    # map address -> index for fast lookup
    idx = {i.address: k for k, i in enumerate(addrs)}
    for e in sorted(entries):
        k = idx.get(e)
        if k is None:
            continue
        body = [addrs[k]]
        ram = set()
        calls = set()
        lits = {}
        j = k
        while j < len(addrs):
            ins = addrs[j]
            if j > k and ins.address in entries and ins.address != e:
                break
            ops = ins.op_str
            # control flow out of line?
            if ins.mnemonic in BRANCH and ins.mnemonic not in ('bl', 'blx'):
                tgt = None
                if ops.startswith('#'):
                    try:
                        tgt = int(ops[1:], 0)
                    except ValueError:
                        tgt = None
                if tgt is not None and tgt != ins.address + ins.size + (
                        (int(ops.split()[-1], 0) if False else 0)):
                    if tgt >= ins.address:
                        pass
                if tgt is not None and (tgt > ins.address + 0x400 or tgt < e):
                    break
            if ins.mnemonic in ('bl', 'blx') and ops.startswith('#'):
                try:
                    calls.add(int(ops[1:], 0) & ~1)
                except ValueError:
                    pass
            t = lit_addr(ins)
            if t is not None and f.base <= t < f.end:
                v = f.rd32(t)
                lits[ins.address] = v
                if 0x20000000 <= v < 0x20060000:
                    ram.add(v)
            # direct register-relative access to a RAM literal already in a reg is
            # not tracked here; that is what z_gh/z_disp are for.
            body.append(ins)
            j += 1
        funcs[e] = {
            'size': sum(x.size for x in body),
            'n': len(body),
            'ram': sorted(ram),
            'calls': sorted(calls),
        }
    os.makedirs(CACHE, exist_ok=True)
    out = os.path.join(CACHE, '%s_funcs.json' % tag)
    json.dump({str(k): v for k, v in funcs.items()}, open(out, 'w'), indent=0)
    print('tag=%s instructions=%d functions=%d -> %s' % (tag, len(addrs), len(funcs), out))
    # positive control
    print('control: funcs containing literal 0x20007400:',
          [hex(k) for k, v in funcs.items() if 0x20007400 in v['ram']][:6])
    tt = [i for i in addrs if i.mnemonic == 'movw' and '0x4e20' in i.op_str]
    print('control: movw #0x4e20 sites:', [hex(i.address) for i in tt])
    return funcs


def load(tag):
    p = os.path.join(CACHE, '%s_funcs.json' % tag)
    if not os.path.exists(p):
        return build(tag)
    return {int(k): v for k, v in json.load(open(p)).items()}


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    cmd = argv[0]
    tag = argv[1]
    f = Fw(tag)
    if cmd == 'build':
        build(tag)
    elif cmd == 'who':
        a = int(argv[2], 0)
        fs = load(tag)
        hits = [(k, v) for k, v in fs.items() if a in v['ram']]
        print('== %s : %d function(s) reference literal 0x%08x' % (tag, len(hits), a))
        for k, v in hits[:40]:
            print('   0x%08x size=%d n=%d' % (k, v['size'], v['n']))
    elif cmd == 'callers':
        a = int(argv[2], 0)
        fs = load(tag)
        hits = [(k, v) for k, v in fs.items() if a in v['calls']]
        print('== %s : %d function(s) CALL 0x%08x' % (tag, len(hits), a))
        for k, v in hits[:40]:
            print('   0x%08x' % k)
    elif cmd == 'list':
        n = int(argv[2]) if len(argv) > 2 else 50
        fs = load(tag)
        for k in sorted(fs)[:n]:
            print('   0x%08x size=%d n=%d' % (k, fs[k]['size'], fs[k]['n']))
    elif cmd == 'dis':
        a = int(argv[2], 0)
        n = int(argv[3]) if len(argv) > 3 else 40
        for i in f.dis(a, n):
            print('   0x%08x  %-14s %s' % (i.address, i.bytes.hex(), i.mnemonic + ' ' + i.op_str))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
