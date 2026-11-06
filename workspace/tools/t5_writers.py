# T5: enumerate writes to descriptor fields +0x230 (0x6062) and +0x238 (0x6064)
# true flash addr = 0x08010000 + file offset ; ELF vaddr should already be true.
import struct, sys
from capstone import *
from capstone.arm import *

BASE = r"D:\mydata\workspace\data\servo_fw_samples\elf"
FILES = {"D8": BASE + r"\v328d8.elf", "3150": BASE + r"\v3150.elf"}

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

def analyze(path):
    data = open(path, 'rb').read()
    ss = sections(data)
    execs = [s for s in ss if (s['flags'] & 0x4) and s['typ'] == 1 and s['size'] > 0]
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    insns = []
    seen = set()
    for s in execs:
        code = data[s['offset']:s['offset'] + s['size']]
        for i in md.disasm(code, s['addr']):
            if i.address in seen: continue
            seen.add(i.address)
            insns.append(i)
    insns.sort(key=lambda x: x.address)
    return data, ss, insns

def memdisp(insn):
    """return list of (operand_index, base_reg, disp) for memory operands with disp"""
    res = []
    for k, op in enumerate(insn.operands):
        if op.type == ARM_OP_MEM:
            res.append((k, op.mem.base, op.mem.disp))
    return res

def describe(insn):
    return "%08X  %-8s %s" % (insn.address, insn.mnemonic, insn.op_str)

TARGETS = (0x230, 0x238)

def scan(tag, path):
    data, ss, insns = analyze(path)
    print("=" * 100)
    print("### %s  %s" % (tag, path))
    print("sections(exec):", [(s['sname'], hex(s['addr']), hex(s['size'])) for s in ss if (s['flags'] & 0x4) and s['typ'] == 1 and s['size']])
    print("insn count:", len(insns), " range", hex(insns[0].address), hex(insns[-1].address))
    # function starts: bl targets + push{..lr}
    starts = set()
    for i in insns:
        if i.mnemonic in ('bl', 'blx') and i.operands and i.operands[0].type == ARM_OP_IMM:
            starts.add(i.operands[0].imm & ~1)
        if i.mnemonic.startswith('push') and 'lr' in i.op_str:
            starts.add(i.address & ~1)
    starts = sorted(starts)
    import bisect
    def func_of(a):
        k = bisect.bisect_right(starts, a) - 1
        return starts[k] if k >= 0 else 0
    callers = {}
    for i in insns:
        if i.mnemonic in ('bl', 'blx') and i.operands and i.operands[0].type == ARM_OP_IMM:
            t = i.operands[0].imm & ~1
            callers.setdefault(t, []).append(i.address)
    idx = {i.address: n for n, i in enumerate(insns)}

    hits = []
    for i in insns:
        md_ = memdisp(i)
        for k, b, d in md_:
            if d in TARGETS and (i.mnemonic.startswith('str') or i.mnemonic.startswith('vstr') or i.mnemonic.startswith('stm')):
                hits.append((i.address, d, 'direct', i))
        # add rX, rY, #imm  then nearby store to rX
        if i.mnemonic.startswith('add') and len(i.operands) >= 3 and i.operands[2].type == ARM_OP_IMM and i.operands[2].imm in TARGETS:
            dst = i.reg_name(i.operands[0].reg)
            n = idx[i.address]
            for j in range(n + 1, min(n + 9, len(insns))):
                jj = insns[j]
                if jj.mnemonic.startswith('str') and jj.operands:
                    bp = jj.operands[1] if len(jj.operands) > 1 else None
                    if bp is not None and bp.type == ARM_OP_MEM and jj.reg_name(bp.mem.base) == dst:
                        hits.append((jj.address, i.operands[2].imm, 'via-add@%08X' % i.address, jj))
                        break
    print("--- hits (disp 0x230/0x238 stores) ---")
    for a, d, how, insn in hits:
        print("%s  field=+0x%X  %s   func=%08X  callers_of_func=%s" % (
            describe(insn), d, how, func_of(a),
            ",".join("%08X" % c for c in callers.get(func_of(a), [])[:8])))
    print("--- context windows ---")
    printed = set()
    for a, d, how, insn in hits:
        f = func_of(a)
        if f in printed: continue
        printed.add(f)
        lo = max(0, idx[f] - 2)
        hi = min(len(insns), idx[f] + 60)
        print("  [func %08X] callers: %s" % (f, ",".join("%08X" % c for c in callers.get(f, [])[:12])))
        for j in range(lo, hi):
            mark = " <<<" if insns[j].address in [h[0] for h in hits] else ""
            print("    " + describe(insns[j]) + mark)
    return hits, func_of, callers, insns, idx

if __name__ == '__main__':
    for tag, p in FILES.items():
        scan(tag, p)
