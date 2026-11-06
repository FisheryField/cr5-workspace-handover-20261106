"""z_tool.py -- instruction-level toolkit for the two DS121 servo images.

Address convention (verified against the known version strings):
    ELF .text vaddr  ==  Ghidra project coordinate
    TRUE flash addr  =  vaddr + 0x10000

Subcommands
  hits [off ...]        real field accesses (base reg != pc, != sp) for the offsets,
                        with enclosing-function estimate from bl-target set
  dump  lo hi [lo hi..] disassembly of ranges (lo/hi in TRUE addresses)
  fnf   lo hi [off ..]  all memory accesses inside a function range, grouped by offset
"""
import sys, struct
from capstone import *
from capstone.arm import *

ELF = {
    'v328d8': r'D:\mydata\workspace\data\servo_fw_samples\elf\v328d8.elf',
    'v3150':  r'D:\mydata\workspace\data\servo_fw_samples\elf\v3150.elf',
}
OFF = 0x10000  # true = vaddr + OFF

def load(path):
    d = open(path, 'rb').read()
    shoff = struct.unpack_from('<I', d, 0x20)[0]
    shnum = struct.unpack_from('<H', d, 0x30)[0]
    shstr = struct.unpack_from('<H', d, 0x32)[0]
    sh = lambda i: struct.unpack_from('<10I', d, shoff + i * 40)
    st = sh(shstr)
    nm = {}
    for i in range(shnum):
        s = sh(i)
        e = d.index(b'\x00', st[4] + s[0])
        nm[d[st[4] + s[0]:e].decode()] = s
    t = nm['.text']
    return d, t[4], t[3], t[5]   # data, fileoff, vaddr, size

def dis(path):
    d, off, va, sz = load(path)
    code = d[off:off + sz]
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB); md.detail = True; md.skipdata = True
    insns = []
    for i in md.disasm(code, va):
        insns.append(i)
    return insns

def fnstarts(insns):
    s = set()
    for i in insns:
        if i.id and i.mnemonic in ('bl', 'blx') and i.operands and i.operands[0].type == ARM_OP_IMM:
            t = i.operands[0].imm
            if 0x08000000 <= t < 0x08060000:
                s.add(t)
    return sorted(s)

import bisect
def enclosing(starts, a, insns):
    j = bisect.bisect_right(starts, a) - 1
    if j < 0:
        return None, None
    return starts[j], a - starts[j]

def real_accesses(insns, targets):
    res = {t: [] for t in targets}
    for i in insns:
        if not i.id:
            continue
        for op in i.operands:
            if op.type == ARM_OP_MEM and op.mem.disp in res:
                if op.mem.base in (ARM_REG_PC, 0) or op.mem.base == ARM_REG_SP:
                    continue
                res[op.mem.disp].append(i)
    return res

CMD = sys.argv[1]
DEFAULT = [0x24c, 0x238, 0x234, 0x230, 0x22c, 0x20c, 0x1ae, 0x1af, 0x2a4,
           0x31f, 0x30, 0x36, 0xa8, 0xb0, 0x1c]

for name, path in ELF.items():
    insns = dis(path)
    print('#' * 78)
    print('#', name, 'insns', len(insns))
    if CMD == 'callers':
        tgs = [int(x, 0) - OFF for x in sys.argv[2:]]
        pushes = [i.address for i in insns
                  if i.id and i.mnemonic.startswith('push') and 'lr' in i.op_str]
        for t in tgs:
            sites = []
            for i in insns:
                if i.id and i.mnemonic in ('bl', 'blx') and i.operands \
                        and i.operands[0].type == ARM_OP_IMM and i.operands[0].imm == t:
                    sites.append(i.address)
            print('  callers of true %08x : %d' % (t + OFF, len(sites)))
            for s in sorted(sites):
                import bisect as _b
                k = _b.bisect_right(pushes, s) - 1
                fs = pushes[k] if k >= 0 else None
                print('     bl@true %08x   enclosing-push@true %s' %
                      (s + OFF, ('%08x' % (fs + OFF)) if fs else '?'))
        continue
    if CMD == 'hits':
        tg = [int(x, 0) for x in sys.argv[2:]] or DEFAULT
        st = fnstarts(insns)
        r = real_accesses(insns, tg)
        for t in tg:
            lst = r.get(t, [])
            w = [i for i in lst if i.mnemonic.startswith('str')]
            print('  +0x%03x : %d real accesses (%d writes)' % (t, len(lst), len(w)))
            for i in lst:
                f, dl = enclosing(st, i.address, insns)
                kind = 'W' if i.mnemonic.startswith('str') else 'R'
                print('    %s true=%08x ghidra=%08x  fn~%s (+0x%x)  %-9s %s' %
                      (kind, i.address + OFF, i.address,
                       ('%08x' % (f + OFF)) if f else '?',
                       dl if dl is not None else 0, i.mnemonic, i.op_str))
    elif CMD == 'dump':
        args = [int(x, 0) for x in sys.argv[2:]]
        for k in range(0, len(args), 2):
            lo, hi = args[k] - OFF, args[k + 1] - OFF
            print('  ---- dump true %08x..%08x ----' % (lo + OFF, hi + OFF))
            for i in insns:
                if lo <= i.address < hi:
                    print('    true=%08x gh=%08x  %-9s %-30s %s' %
                          (i.address + OFF, i.address, i.mnemonic, i.op_str, i.bytes.hex()))
    elif CMD == 'fnf':
        lo, hi = int(sys.argv[2], 0) - OFF, int(sys.argv[3], 0) - OFF
        tg = [int(x, 0) for x in sys.argv[4:]] or None
        grp = {}
        for i in insns:
            if not (lo <= i.address < hi) or not i.id:
                continue
            for op in i.operands:
                if op.type == ARM_OP_MEM:
                    if op.mem.base in (ARM_REG_PC, 0) or op.mem.base == ARM_REG_SP:
                        continue
                    off = op.mem.disp
                    if tg is not None and off not in tg:
                        continue
                    grp.setdefault(off, []).append(i)
        for off in sorted(grp):
            lst = grp[off]
            rd = len([i for i in lst if not i.mnemonic.startswith('str')])
            wr = len(lst) - rd
            print('    +0x%03x  R=%d W=%d  sites=%s' %
                  (off, rd, wr, ','.join('%08x' % (i.address + OFF) for i in lst)))
