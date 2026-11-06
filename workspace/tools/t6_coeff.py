#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T6: trace RAM struct base 0x2000C1D8 in v3150 (and its D8 counterpart).

subcommands
  hdr <elf>
  refs <elf> <hexconst> [maxdump]   -> literal-pool sites + pc-relative xref instructions
  dis  <elf> <hexaddr> <n>
  dump <elf> <hexaddr> <nwords>
"""
import sys, struct
from capstone import *

def load(path):
    d = open(path, 'rb').read()
    if d[:4] != b'\x7fELF':
        raise SystemExit('not ELF')
    is32 = d[4] == 1
    le = d[5] == 1
    e_phoff = struct.unpack_from('<I', d, 0x1C)[0]
    e_phentsize = struct.unpack_from('<H', d, 0x2A)[0]
    e_phnum = struct.unpack_from('<H', d, 0x2C)[0]
    segs = []
    for i in range(e_phnum):
        o = e_phoff + i * e_phentsize
        p_type, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_flags, p_align = \
            struct.unpack_from('<8I', d, o)
        if p_type == 1:  # PT_LOAD
            segs.append((p_vaddr, p_offset, p_filesz, p_memsz, p_flags))
    e_entry = struct.unpack_from('<I', d, 0x18)[0]
    return d, segs, e_entry

def rd(d, segs, addr, n):
    for va, off, fsz, msz, fl in segs:
        if va <= addr < va + fsz:
            o = off + (addr - va)
            return d[o:o + n]
    return None

def readwords(d, segs, addr, n):
    b = rd(d, segs, addr, 4 * n)
    if b is None:
        return None
    return list(struct.unpack_from('<%dI' % n, b, 0))

def axdis(segs, va, size):
    out = []
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN | CS_MODE_MCLASS)
    md.detail = True
    for sva, soff, fsz, msz, fl in segs:
        if not (fl & 1):
            continue
        if not (sva < va + size and va < sva + fsz):
            continue
        start = max(va, sva)
        o = soff + (start - sva)
        buf = d[o:o + min(size - (start - va), sva + fsz - start)]
        out.extend(md.disasm(buf, start))
    return out

def find_lits(d, segs, const):
    """returns list of (lit_addr, seg) where 4-byte LE word == const"""
    hits = []
    cb = struct.pack('<I', const)
    for sva, soff, fsz, msz, fl in segs:
        blob = d[soff:soff + fsz]
        start = 0
        while True:
            i = blob.find(cb, start)
            if i < 0:
                break
            if i % 4 == 0:
                hits.append(sva + i)
            start = i + 1
    return hits

def xrefs_to(d, segs, targets):
    tset = set(targets)
    res = []
    for sva, soff, fsz, msz, fl in segs:
        if not (fl & 1):
            continue
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN | CS_MODE_MCLASS)
        md.detail = True
        buf = d[soff:soff + fsz]
        for ins in md.disasm(buf, sva):
            tgt = None
            if ins.mnemonic.startswith('ldr') or ins.mnemonic.startswith('adr'):
                for op in ins.operands:
                    if op.type == ARM_OP_MEM and op.mem.base == ARM_REG_PC:
                        tgt = ((ins.address + 4) & ~3) + op.mem.disp
                    elif op.type == ARM_OP_IMM and ins.mnemonic.startswith('adr'):
                        tgt = op.imm
            if tgt in tset:
                res.append((ins.address, ins.mnemonic + ' ' + ins.op_str, tgt))
    return res

def find_movwt(d, segs, const):
    hi = (const >> 16) & 0xFFFF
    lo = const & 0xFFFF
    res = []
    for sva, soff, fsz, msz, fl in segs:
        if not (fl & 1):
            continue
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN | CS_MODE_MCLASS)
        md.detail = True
        for ins in md.disasm(d[soff:soff + fsz], sva):
            if ins.mnemonic in ('movw', 'movt', 'mov.w') and ins.operands:
                for op in ins.operands:
                    if op.type == ARM_OP_IMM and op.imm in (hi, lo):
                        res.append((ins.address, ins.mnemonic + ' ' + ins.op_str))
    return res

if __name__ == '__main__':
    cmd = sys.argv[2]
    d, segs, entry = load(sys.argv[1])
    if cmd == 'hdr':
        print('entry %08X' % entry)
        for sva, soff, fsz, msz, fl in segs:
            print('LOAD va %08X off %08X filesz %08X memsz %08X fl %d' % (sva, soff, fsz, msz, fl))
    elif cmd == 'refs':
        c = int(sys.argv[3], 16)
        maxd = int(sys.argv[4]) if len(sys.argv) > 4 else 12
        lits = find_lits(d, segs, c)
        print('const %08X : literal-pool sites = %d' % (c, len(lits)))
        for a in lits[:40]:
            print('   lit @ %08X' % a)
        xr = xrefs_to(d, segs, lits)
        print('pc-relative xrefs = %d' % len(xr))
        for a, t, g in xr[:80]:
            print('   %08X  %-30s -> %08X' % (a, t, g))
        mw = find_movwt(d, segs, c)
        if mw:
            print('movw/movt candidates = %d' % len(mw))
            for a, t in mw[:20]:
                print('   %08X %s' % (a, t))
    elif cmd == 'dis':
        a = int(sys.argv[3], 16)
        n = int(sys.argv[4])
        ins = axdis(segs, a, n * 4)
        for i in ins[:n]:
            raw = ' '.join('%02x' % b for b in i.bytes)
            print('%08X  %-10s %-28s ; %s' % (i.address, raw, i.mnemonic + ' ' + i.op_str, ''))
    elif cmd == 'dump':
        a = int(sys.argv[3], 16)
        n = int(sys.argv[4])
        w = readwords(d, segs, a, n)
        if w is None:
            print('addr %08X not in any LOAD segment (RAM, not in image)' % a)
        else:
            for i in range(0, n, 4):
                print('%08X: %s' % (a + 4 * i, ' '.join('%08X' % x for x in w[i:i + 4])))
