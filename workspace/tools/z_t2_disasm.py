# -*- coding: utf-8 -*-
# T2: independent re-read of the +0x234 (=0x6063) construction in v328d8 / v3150
import struct, re, sys
from capstone import *
from capstone.arm import *

PATHS = {
 'D8':   r'D:\mydata\workspace\data\servo_fw_samples\elf\v328d8.elf',
 '3150': r'D:\mydata\workspace\data\servo_fw_samples\elf\v3150.elf',
}
SITE234 = {'D8': 0x080155EC, '3150': 0x08014B04}
SITE238 = {'D8': 0x08015602, '3150': 0x08014B62}
TBL     = {'D8': 0x20000078, '3150': 0x20000074}
CORR    = {'D8': None, '3150': 0x20003DB0}

def load_elf(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'\x7fELF', 'not ELF'
    e_phoff = struct.unpack_from('<I', d, 0x1C)[0]
    e_phentsize = struct.unpack_from('<H', d, 0x2A)[0]
    e_phnum = struct.unpack_from('<H', d, 0x2C)[0]
    segs = []
    for i in range(e_phnum):
        v = struct.unpack_from('<IIIIIIII', d, e_phoff + i*e_phentsize)
        if v[0] == 1:
            segs.append((v[2], v[1], v[4]))   # vaddr, offset, filesz
    return d, segs

class Img:
    def __init__(self, name, path):
        self.name = name
        self.data, self.segs = load_elf(path)
        self.md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        self.md.detail = True
    def read(self, vaddr, n):
        for v, o, sz in self.segs:
            if v <= vaddr < v + sz:
                k = vaddr - v
                return self.data[o+k:o+k+n]
        return None
    def code_segs(self):
        return [(v, o, sz) for (v, o, sz) in self.segs if sz > 0x1000]

img = {k: Img(k, p) for k, p in PATHS.items()}

print('=== SEGMENTS (vaddr, off, filesz) ===')
for k, i in img.items():
    print(k, [(hex(a), hex(b), hex(c)) for a, b, c in i.segs])

def lit_target(ins):
    m = re.match(r'^(\w+),\s*\[pc,\s*#(-?0x[0-9a-f]+)\]$', ins.op_str)
    if not m:
        return None
    off = int(m.group(2), 16)
    tgt = ((ins.address + 4) & ~3) + off
    return m.group(1), tgt

def fmt(ins, extra=''):
    return '  %08x  %-24s %s %s%s' % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, extra)

def listing(i, start, end, resolve_lit=True):
    code = i.read(start, end - start)
    if code is None:
        print('  !! no bytes for %08x-%08x' % (start, end)); return []
    out = []
    for ins in i.md.disasm(code, start):
        ex = ''
        lt = lit_target(ins)
        if lt and resolve_lit:
            r, t = lt
            val = i.read(t, 4)
            sv = ('0x%08x' % struct.unpack('<I', val)[0]) if val and len(val) == 4 else '??'
            ex = '   ; %s = [%08x] = %s' % (r, t, sv)
        out.append(ins)
        print(fmt(ins, ex))
    return out

# ---------------- Section A: the +0x234 / +0x238 blocks ----------------
for k in ('D8', '3150'):
    i = img[k]
    s = SITE234[k]
    print('\n=== A[%s] window %08x .. %08x  (site234=%08x site238=%08x) ===' %
          (k, s-0x90, SITE238[k]+0x10, s, SITE238[k]))
    listing(i, s-0x90, SITE238[k]+0x10)

# ---------------- Section B: prologue candidates ----------------
for k in ('D8', '3150'):
    i = img[k]
    s = SITE234[k]
    print('\n=== B[%s] push/prologue candidates in [%08x,%08x) ===' % (k, s-0x500, s-0x40))
    code = i.read(s-0x500, 0x500-0x40)
    ins_list = list(i.md.disasm(code, s-0x500)) if code else []
    for n, ins in enumerate(ins_list):
        if ins.mnemonic.startswith('push'):
            prev = ins_list[n-1] if n else None
            print('  push @%08x  %s %s      prev: %s' % (ins.address, ins.mnemonic, ins.op_str,
                  ('%08x %s %s' % (prev.address, prev.mnemonic, prev.op_str)) if prev else '-'))

# ---------------- Section C: stores to [sp,#0x10..0x1c] ----------------
for k in ('D8', '3150'):
    i = img[k]
    s = SITE234[k]
    print('\n=== C[%s] stores to [sp,#0x10..0x1f] in [%08x,%08x) with 7 prior instrs ===' % (k, s-0x500, s+0x10))
    code = i.read(s-0x500, 0x510)
    ins_list = list(i.md.disasm(code, s-0x500)) if code else []
    for n, ins in enumerate(ins_list):
        if ins.mnemonic.startswith('str') and re.search(r'\[sp,\s*#0x1[0-9a-f]\]', ins.op_str):
            for j in range(max(0, n-7), n+1):
                mark = ' <<<' if j == n else ''
                print(fmt(ins_list[j], mark))
            print('  ---')

# ---------------- Section D: function pointer table +8 slot ----------------
def whole_code(i):
    out = []
    for v, o, sz in i.code_segs():
        blk = i.data[o:o+sz]
        out.extend(list(i.md.disasm(blk, v)))
    return out

for k in ('D8', '3150'):
    i = img[k]
    tgt = TBL[k]
    lst = whole_code(i)
    idx_of = {ins.address: n for n, ins in enumerate(lst)}
    print('\n=== D[%s] decoder total instrs = %d ; scan for table 0x%08x ===' % (k, len(lst), tgt))
    pat = struct.pack('<I', tgt)
    hits = []
    off = 0
    while True:
        p = i.data.find(pat, off)
        if p < 0: break
        for v, o, sz in i.segs:
            if o <= p < o + sz:
                hits.append(v + (p - o))
        off = p + 1
    print('  dword occurrences in file: %s' % [hex(h) for h in hits])
    loads = []
    for n, ins in enumerate(lst):
        lt = lit_target(ins)
        if lt and lt[1] == tgt:
            val = i.read(lt[1], 4)
            v = struct.unpack('<I', val)[0] if val else 0
            loads.append((n, ins, lt[0], v))
    print('  pc-relative loads yielding 0x%08x: %d' % (tgt, len(loads)))
    for n, ins, reg, v in loads:
        print('    load @%08x  %s %s   -> %s = 0x%08x' % (ins.address, ins.mnemonic, ins.op_str, reg, v))
    # forward trace: does anybody store through it?
    regid = {}
    for n, ins, reg, v in loads:
        rid = None
        for op in ins.operands:
            if op.type == ARM_OP_REG:
                rid = op.reg; break
        wrote = []
        for j in range(n+1, min(n+40, len(lst))):
            x = lst[j]
            rr, rw = x.regs_access()
            if rid in rw:
                break
            for op in x.operands:
                if op.type == ARM_OP_MEM and op.mem.base == rid:
                    kind = 'STORE' if x.mnemonic.startswith('str') or x.mnemonic.startswith('stm') else \
                           ('LOAD' if x.mnemonic.startswith('ldr') or x.mnemonic.startswith('ldm') else 'MEM?')
                    wrote.append('%s @%08x %s %s (disp=0x%x)' % (kind, x.address, x.mnemonic, x.op_str, op.mem.disp))
        print('    trace from %08x (%s): %s' % (ins.address, reg, wrote if wrote else 'no mem access through base within 40 instrs'))

# ---------------- Section E: positive controls ----------------
print('\n=== E positive controls ===')
for k in ('D8', '3150'):
    i = img[k]
    for s in (b'DS.3.1.5.0', b'DS.3.2.D.8'):
        p = i.data.find(s)
        va = None
        if p >= 0:
            for v, o, sz in i.segs:
                if o <= p < o + sz:
                    va = v + (p - o)
        print('  %-5s string %-12s -> %s' % (k, s.decode(), hex(va) if va else 'NOT FOUND'))
    # movw #0x4e20 (20000) sites in window
    lst = listing(i, SITE234[k]-0xa0, SITE234[k]+0x04)
    for ins in lst:
        if 'movw' in ins.mnemonic and ('0x4e20' in ins.op_str or '0x20000' in ins.op_str):
            print('  %s movw-const: %08x %s %s' % (k, ins.address, ins.mnemonic, ins.op_str))
# control: tracer must find the known 3150 correction-term store
for k, tgt in (('3150', CORR['3150']),):
    i = img[k]
    lst = whole_code(i)
    n_hit = 0
    for n, ins in enumerate(lst):
        lt = lit_target(ins)
        if lt and lt[1] == tgt:
            for j in range(n+1, min(n+40, len(lst))):
                x = lst[j]
                for op in x.operands:
                    if op.type == ARM_OP_MEM and x.mnemonic.startswith('str'):
                        n_hit += 1
                        print('  CONTROL %s: store through 0x%08x-base candidate @%08x %s %s' %
                              (k, tgt, x.address, x.mnemonic, x.op_str))
    print('  CONTROL %s: literal-load+store candidates for 0x%08x = %d (expect >=1: 0x08014AF2 str r0,[r1,#0x18])' % (k, tgt, n_hit))
