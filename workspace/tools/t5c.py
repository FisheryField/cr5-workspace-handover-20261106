# T5c: full resync disasm, find all writers to descriptor fields +0x230 / +0x238
import struct, bisect, sys
from capstone import *
from capstone.arm import *

BASE = r"D:\mydata\workspace\data\servo_fw_samples\elf"
FILES = [("D8", BASE + r"\v328d8.elf"), ("3150", BASE + r"\v3150.elf")]
TARGETS = (0x230, 0x238)

def sections(data):
    e_shoff = struct.unpack_from('<I', data, 0x20)[0]
    e_shentsize = struct.unpack_from('<H', data, 0x2E)[0]
    e_shnum = struct.unpack_from('<H', data, 0x30)[0]
    e_shstrndx = struct.unpack_from('<H', data, 0x32)[0]
    out = []
    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        name, typ, flags, addr, offset, size = struct.unpack_from('<IIIIII', data, off)
        out.append(dict(name=name, typ=typ, flags=flags, addr=addr, offset=offset, size=size))
    st = out[e_shstrndx]
    strtab = data[st['offset']:st['offset'] + st['size']]
    for s in out:
        n = s['name']; e = strtab.find(b'\0', n)
        s['sname'] = strtab[n:e].decode('latin1')
    return out

def full_disasm(data, ss):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB); md.detail = True
    insns = []
    for s in ss:
        if not ((s['flags'] & 0x4) and s['typ'] == 1 and s['size']): continue
        code = data[s['offset']:s['offset'] + s['size']]; base = s['addr']
        off = 0; n = len(code)
        while off < n:
            got = False
            for i in md.disasm(code[off:off + 256], base + off):
                insns.append(i); got = True
            if got:
                last = insns[-1]; noff = last.address + last.size - base
                off = noff if noff > off else off + 2
            else:
                off += 2
    insns.sort(key=lambda x: x.address)
    return insns

def memops(insn):
    return [(k, op.mem.base, op.mem.disp) for k, op in enumerate(insn.operands) if op.type == ARM_OP_MEM]

def desc(insn):
    return "%08X  %-8s %s" % (insn.address, insn.mnemonic, insn.op_str)

def scan(tag, path, showctx=True):
    data = open(path, 'rb').read(); ss = sections(data)
    insns = full_disasm(data, ss)
    print("=" * 110)
    print("### %s  %s   insns=%d  range %s..%s" % (tag, path, len(insns), hex(insns[0].address), hex(insns[-1].address)))
    starts = set()
    for i in insns:
        if i.mnemonic in ('bl', 'blx') and i.operands and i.operands[0].type == ARM_OP_IMM:
            starts.add(i.operands[0].imm & ~1)
        if i.mnemonic.startswith('push') and 'lr' in i.op_str:
            starts.add(i.address)
    starts = sorted(starts)
    def func_of(a):
        k = bisect.bisect_right(starts, a) - 1
        return starts[k] if k >= 0 else 0
    callers = {}
    for i in insns:
        if i.mnemonic in ('bl', 'blx') and i.operands and i.operands[0].type == ARM_OP_IMM:
            callers.setdefault(i.operands[0].imm & ~1, []).append(i.address)
    idx = {i.address: n for n, i in enumerate(insns)}
    hits = []
    for i in insns:
        for k, b, d in memops(i):
            if d in TARGETS and (i.mnemonic.startswith('str') or i.mnemonic.startswith('vstr')):
                hits.append((i.address, d, 'imm'))
        if i.mnemonic.startswith('add') and len(i.operands) >= 3 and i.operands[2].type == ARM_OP_IMM and i.operands[2].imm in TARGETS:
            dst = i.reg_name(i.operands[0].reg); n = idx[i.address]
            for j in range(n + 1, min(n + 9, len(insns))):
                jj = insns[j]
                if jj.mnemonic.startswith('str') and len(jj.operands) > 1 and jj.operands[1].type == ARM_OP_MEM \
                   and jj.reg_name(jj.operands[1].mem.base) == dst:
                    hits.append((jj.address, i.operands[2].imm, 'viaadd@%08X' % i.address)); break
    print("--- HITS ---")
    for a, d, how in hits:
        f = func_of(a)
        print("%s  field=+0x%X [%s]  func=%08X callers=%s" % (desc(next(x for x in insns if x.address == a)), d, how, f,
              ",".join("%08X" % c for c in callers.get(f, [])[:10])))
    if showctx:
        print("--- FUNC CONTEXT (unique funcs containing hits) ---")
        done = set()
        for a, d, how in hits:
            f = func_of(a)
            if f in done: continue
            done.add(f)
            print("  [func %08X] callers: %s" % (f, ",".join("%08X" % c for c in callers.get(f, [])[:12])))
            lo = max(0, idx.get(f, 0)); hi = min(len(insns), lo + 90)
            for j in range(lo, hi):
                m = " <<<" if insns[j].address in [h[0] for h in hits] else ""
                print("    " + desc(insns[j]) + m)
    return insns, hits

if __name__ == '__main__':
    # 1) patch-byte address-convention check (3150 §31 patch point)
    for tag, p in FILES:
        d = open(p, 'rb').read(); ss = sections(d)
        txt = [s for s in ss if s['sname'] == '.text'][0]
        for va in (0x08014AFE, 0x08024AFE):
            off = txt['offset'] + (va - txt['addr'])
            print("CHECK %s vaddr %08X bytes %s" % (tag, va, d[off:off + 6].hex() if 0 <= off < len(d) - 6 else 'n/a'))
    for tag, p in FILES:
        scan(tag, p)
