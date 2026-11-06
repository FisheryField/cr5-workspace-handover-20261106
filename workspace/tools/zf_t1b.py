#!/usr/bin/env python3
"""zf_t1b.py -- T1 layer-2 census (v4).  TRUE addr = 0x08010000 + file offset.

Fix vs v3: `add.w rD, rB, rS, lsl #n` keeps the base-relative tracking
(otherwise the encoder-init function's own [r8,#0x24] access is invisible).
"""
import sys, os, json, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from z_fw import Fw

ROOT = os.path.dirname(HERE)
CACHE = os.path.join(ROOT, '.zwork')

BASES = {
    '3150': {'A': 0x200073A0, 'B': 0x20007400, 'C': 0x20007660,
             'desc': 0x2000129C, 'fpt': 0x20000074},
    'd8':   {'A': 0x200074C8, 'B': 0x20007528, 'C': 0x20007B30,
             'desc': 0x2000138C, 'fpt': 0x20000078},
}
PERSIST_FUNC = {'3150': 0x08011748, 'd8': 0x08011708}
ENC_INIT = {'3150': 0x08021730, 'd8': 0x08021F7C}
DESC_OFFS = {0x238: '6064', 0x230: '6062', 0x24C: '607A', 0x20C: '607C',
             0x1AE: '6040', 0x1AF: '6041', 0x22C: '6060', 0x2A4: '6098'}
_MD = None


def hx(a):
    return '%08x' % a if a is not None else '?'


def md():
    global _MD
    if _MD is None:
        from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
        _MD = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
        _MD.detail = True
        _MD.skipdata = True
    return _MD


def dis(f, addr, count=90):
    o = f.off(addr)
    out = []
    try:
        for i in md().disasm(f.code[o:o + count * 6], addr):
            out.append(i)
            if len(out) >= count:
                break
    except Exception:
        pass
    return out


def cache(t):
    return json.load(open(os.path.join(CACHE, '%s_sweep.json' % t)))


def enclosing(pushes, a, span=0x1400):
    c = []
    for p in pushes:
        p = int(p, 16) if isinstance(p, str) else p
        if p <= a and a - p < span:
            c.append(p)
    return max(c) if c else None


def mem_ops(insn):
    out = []
    if insn.mnemonic.startswith('.') or not insn.id:
        return out
    try:
        ops = insn.operands
    except Exception:
        return out
    for k, op in enumerate(ops):
        if op.type == 3:
            b = op.mem.base
            try:
                bn = insn.reg_name(b) if b else ''
            except Exception:
                bn = ''
            out.append((k, bn, op.mem.disp))
    return out


def sites_using_reg(f, site, reg, window=90):
    reads, writes, derived = [], [], []
    cur = {reg: 0}
    for i in dis(f, site, window):
        if i.address == site:
            continue
        if i.mnemonic in ('add', 'add.w', 'addw', 'adds') and len(i.operands) == 3:
            d, s1, s2 = i.operands
            try:
                dn = i.reg_name(d.reg)
                b = i.reg_name(s1.reg)
            except Exception:
                dn = b = None
            if b in cur and dn:
                if s2.type == 2:
                    cur[dn] = cur[b] + s2.imm
                    derived.append(cur[dn])
                elif s2.type == 1 and s2.shift.type != 0:
                    cur[dn] = cur[b]          # indexed: keep base-relative
                    derived.append(('base', cur[b]))
        for k, bn, disp in mem_ops(i):
            if bn in cur:
                (writes if k == 0 else reads).append((cur[bn] + disp, i.address, i.mnemonic))
    return reads, writes, derived


def decode_reg(f, a):
    ins = dis(f, a, 1)
    i0 = ins[0]
    if i0.mnemonic.startswith('.'):
        raise ValueError('skipdata')
    return i0, i0.reg_name(i0.operands[0].reg)


def base_funcs(t, base, window=90):
    f = Fw(t)
    c = cache(t)
    out = {}
    for s, p in c['lit'].get(hx(base), []):
        a = int(s, 16)
        fs = enclosing(c['pushes'], a)
        try:
            i0, reg = decode_reg(f, a)
        except Exception as e:
            out.setdefault(fs, {'err': []})['err'].append((s, str(e)))
            continue
        r, w, dv = sites_using_reg(f, a, reg, window)
        d = out.setdefault(fs, {'sites': [], 'reads': set(), 'writes': set(),
                                'der': set(), 'err': []})
        d['sites'].append(s)
        d['reads'].update(o for o, _, _ in r)
        d['writes'].update(w)
        d['der'].update(dv)
    return out


def cmd_C(t):
    c = cache(t)
    ei = ENC_INIT[t]
    cs = c['calls'].get(hx(ei), [])
    print('== [%s] encoder-init %s callers: %d %s' % (t, hx(ei), len(cs), ' '.join(cs)))
    for s in cs:
        own = enclosing(c['pushes'], int(s, 16))
        print('   site %s in func %s ; callers of that func: %s'
              % (s, hx(own), c['calls'].get(hx(own), [])[:12] if own else []))


def cmd_B(t):
    print('== [%s] block A %s ==' % (t, hx(BASES[t]['A'])))
    for fs, d in sorted(base_funcs(t, BASES[t]['A']).items(),
                        key=lambda kv: (kv[0] is None, kv[0])):
        if 'sites' not in d:
            print('   func %s ERR %s' % (hx(fs), d['err']))
            continue
        print('   func %s sites=%s' % (hx(fs), ','.join(d['sites'])))
        print('        R: %s' % ' '.join('+0x%x' % o for o in sorted(d['reads'])))
        print('        W: %s' % ' '.join('%s@+0x%x' % (mn, o) for o, ad, mn in sorted(d['writes'])))


def cmd_R2(t):
    print('== [%s] OD field accesses (desc base %s) ==' % (t, hx(BASES[t]['desc'])))
    f = Fw(t)
    seen = set()
    for s, p in cache(t)['lit'].get(hx(BASES[t]['desc']), []):
        a = int(s, 16)
        try:
            i0, reg = decode_reg(f, a)
        except Exception as e:
            print('   site %s ERR %s' % (s, e))
            continue
        fs = enclosing(cache(t)['pushes'], a)
        r, w, dv = sites_using_reg(f, a, reg, window=140)
        for kind, lst in (('W', w), ('R', r)):
            for o, ad, mn in sorted(lst):
                if o in DESC_OFFS and (ad, kind) not in seen:
                    seen.add((ad, kind))
                    print('   %s %s %-9s %-6s +0x%-4x func %s'
                          % (kind, hx(ad), mn, DESC_OFFS[o], o, hx(fs)))


CMDS = {'C': cmd_C, 'B': cmd_B, 'R2': cmd_R2}

if __name__ == '__main__':
    for t in ('3150', 'd8'):
        for k in sys.argv[1:]:
            try:
                CMDS[k](t)
            except Exception:
                traceback.print_exc()
