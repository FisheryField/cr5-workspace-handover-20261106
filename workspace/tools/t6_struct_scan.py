#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T6 v2: locate the axis-indexed coefficient struct (base + axis*stride) in both servo builds.

WHY v2: tools/t6_coeff.py assumes PT_LOAD program headers; v3150.elf/v328d8.elf have
NONE (hdr prints no LOAD lines) -> it silently returned "0 sites" while the disassembly
plainly showed lit@08014B90 = 2000C1D8.  This version parses SECTION headers and
FAILS LOUDLY if its two hard-coded positive controls are not reproduced.

usage: t6_struct_scan.py <elf> <hexconst> [lit-vaddr=xref-vaddr ...]
"""
import sys, struct
from capstone import *
from capstone.arm import *

STORE = {'str', 'strh', 'strb', 'strd', 'vstr', 'strt', 'push', 'stm', 'stmia', 'stmdb'}
LOAD = {'ldr', 'ldrh', 'ldrb', 'ldrsb', 'ldrsh', 'ldrd', 'vldr', 'ldrt', 'pop', 'ldm', 'ldmia'}


def load(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'\x7fELF', 'not ELF'
    assert d[4] == 1 and d[5] == 1, 'need ELF32 LE'
    e_shoff = struct.unpack_from('<I', d, 0x20)[0]
    e_shentsize = struct.unpack_from('<H', d, 0x2E)[0]
    e_shnum = struct.unpack_from('<H', d, 0x30)[0]
    e_shstrndx = struct.unpack_from('<H', d, 0x32)[0]
    shs = []
    for i in range(e_shnum):
        o = e_shoff + i * e_shentsize
        nm, typ, fl, addr, off, size = struct.unpack_from('<6I', d, o)
        shs.append(dict(nm=nm, typ=typ, fl=fl, addr=addr, off=off, size=size))
    stro = shs[e_shstrndx]['off']
    for s in shs:
        e = d.index(b'\0', stro + s['nm'])
        s['sname'] = d[stro + s['nm']:e].decode('latin1')
    return d, shs


def lit_sites(d, shs, const):
    cb = struct.pack('<I', const)
    out = []
    for s in shs:
        if s['typ'] != 1 or s['addr'] == 0 or s['size'] == 0:
            continue
        blob = d[s['off']:s['off'] + s['size']]
        i = 0
        while True:
            i = blob.find(cb, i)
            if i < 0:
                break
            if i % 4 == 0:
                out.append(s['addr'] + i)
            i += 1
    return out


def dis_all(d, shs):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN | CS_MODE_MCLASS)
    md.detail = True
    ins = []
    for s in shs:
        if s['typ'] != 1 or not (s['fl'] & 0x4) or s['addr'] == 0 or s['size'] == 0:
            continue
        ins.extend(list(md.disasm(d[s['off']:s['off'] + s['size']], s['addr'])))
    return ins


def pc_target(i):
    for op in i.operands:
        if op.type == ARM_OP_MEM and op.mem.base == ARM_REG_PC:
            return ((i.address + 4) & ~3) + op.mem.disp
        if op.type == ARM_OP_IMM and i.mnemonic.startswith('adr'):
            return op.imm
    return None


def txt(i):
    return '%08X  %-24s' % (i.address, i.mnemonic + ' ' + i.op_str)


def classify(ins_all, pos, start_idx, dest, span=0x600, maxn=400):
    """one-step propagation of the struct pointer register; returns (events, stop)."""
    regs = {dest} if dest is not None else set()
    ev = []
    end = min(len(ins_all), start_idx + maxn)
    for k in range(start_idx, end):
        i = ins_all[k]
        if i.address - ins_all[start_idx].address > span:
            break
        mn = i.mnemonic.split('.')[0]
        for op in i.operands:
            if op.type == ARM_OP_MEM and op.mem.base in regs:
                kind = 'W' if mn in STORE else ('R' if mn in LOAD else '?')
                ev.append((i.address, kind, op.mem.disp, i.mnemonic + ' ' + i.op_str, k - start_idx))
        if mn in ('pop', 'bx') and 'pc' in i.op_str:
            break
        wl = i.regs_write
        if not wl:
            continue
        dst = wl[0]
        if mn in ('add', 'adds', 'addw', 'adr', 'sub', 'subs', 'rsb'):
            srcs = [o.reg for o in i.operands if o.type == ARM_OP_REG]
            if any(r in regs for r in srcs[1:]):
                regs.add(dst)
                ev.append((i.address, 'BASE', 0, 'NEWBASE %s | %s' % (i.reg_name(dst), i.mnemonic + ' ' + i.op_str), k - start_idx))
                continue
        if dst in regs and dst != dest:
            regs.discard(dst)
        if dst == dest and k > start_idx and mn in ('ldr', 'ldrh', 'ldrb', 'mov', 'movs'):
            regs.discard(dst)
    return ev


def main():
    elf = sys.argv[1]
    const = int(sys.argv[2], 16)
    controls = [tuple(int(x, 16) for x in a.split('=')) for a in sys.argv[3:]]
    d, shs = load(elf)
    print('== %s  const %08X' % (elf, const))
    execs = [s['sname'] for s in shs if s['typ'] == 1 and (s['fl'] & 0x4) and s['size']]
    print('   exec sections: %s' % ', '.join(execs))
    lits = set(lit_sites(d, shs, const))
    print('   literal sites: %d' % len(lits))
    ins = dis_all(d, shs)
    print('   decoded insns: %d' % len(ins))
    pos = {i.address: k for k, i in enumerate(ins)}

    # ---- positive control: known (lit, xref) pairs must be reproduced ----
    ok = True
    for lit, xr in controls:
        got = pos.get(xr)
        good = False
        if lit in lits and got is not None and got > 0:
            prev = ins[got - 1] if ins[got-1].address == xr else None
            i = ins[got]
            good = i.mnemonic.startswith('ldr') and pc_target(i) == lit
        print('   [CTRL] lit %08X xref %08X -> %s' % (lit, xr, 'OK' if good else 'FAIL'))
        ok = ok and good
    if not ok:
        print('   POSITIVE CONTROL FAILED - refusing to report')
        sys.exit(2)

    xr = []
    for i in ins:
        if not i.mnemonic.startswith('ldr'):
            continue
        t = pc_target(i)
        if t in lits:
            xr.append((i, t, i.regs_write[0] if i.regs_write else None))
    print('   pc-relative xrefs to those literals: %d' % len(xr))

    for i, lit, dest in xr:
        k = pos[i.address]
        print('\n--- site %08X  lit %08X  dest %s' % (i.address, lit, i.reg_name(dest) if dest else '?'))
        for j in range(k, min(len(ins), k + 4)):
            print('      ' + txt(ins[j]))
        ev = classify(ins, pos, k, dest)
        seen = {}
        for a, kind, disp, t, off in ev:
            key = (kind, disp)
            if key not in seen:
                seen[key] = [a, t, 1]
            else:
                seen[key][2] += 1
        if not ev:
            print('      (no base-relative access found in window)')
        for (kind, disp), (a, t, n) in sorted(seen.items(), key=lambda x: (x[1][0])):
            print('      %s  +0x%03X  x%-2d  first %08X  %s' % (kind, disp, n, a, t))


main()
