#!/usr/bin/env python3
"""T3 step 4: field-access census over 0x60-stride per-axis blocks.

Tracks registers that hold  <RAM literal base> + <something>*0x60  and reports
every memory access offset on them.  Also reports literal loads of FLASH
addresses in the same window (candidate parameter source table) and `bl` calls
carrying a block pointer (candidate memcpy / init call).

Addresses printed are TRUE flash addresses (= ELF address + 0x10000).
RAM literal values are printed verbatim (the image bytes are the same in both
coordinate systems).
"""
import struct, sys, collections

ELF = {3150: r"D:\mydata\workspace\data\servo_fw_samples\elf\v3150.elf",
       328: r"D:\mydata\workspace\data\servo_fw_samples\elf\v328d8.elf"}
SHIFT = 0x10000  # ELF/Ghidra -> true flash address


def elf_code(path):
    d = open(path, 'rb').read()
    e_shoff, = struct.unpack_from('<I', d, 0x20)
    e_shentsize, e_shnum = struct.unpack_from('<HH', d, 0x2e)
    for i in range(e_shnum):
        o = e_shoff + i * e_shentsize
        nm, ty, fl, addr, off, sz = struct.unpack_from('<IIIIII', d, o)
        if fl & 0x2 and addr == 0x08000000:
            return d[off:off + sz]
    raise SystemExit("no section")


def decode(code):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.skipdata = True
    return list(md.disasm(code, 0x08000000))


def litval(ins, code):
    if ins.mnemonic.startswith('ldr') and '[pc' in ins.op_str:
        try:
            off = int(ins.op_str.split('#')[-1].rstrip(']'), 0)
        except ValueError:
            return None
        t = ((ins.address + 4) & ~3) + off
        if 0x08000000 <= t <= 0x08000000 + len(code) - 4:
            return struct.unpack_from('<I', code, t - 0x08000000)[0]
    return None


def memacc(ins):
    """return (basereg, offset_bytes) for a plain memory access, else None"""
    if ins.mnemonic not in ('ldr', 'ldrb', 'ldrh', 'ldrsb', 'ldrsh', 'str',
                            'strb', 'strh', 'vldr', 'vstr', 'ldrd', 'strd'):
        return None
    op = ins.op_str
    if '[' not in op:
        return None
    mem = op[op.index('['):]
    if not mem.endswith(']'):
        return None
    inner = mem[1:-1]
    parts = [p.strip() for p in inner.split(',')]
    base = parts[0]
    if not base.startswith('r') and not base.startswith('sp'):
        return None
    off = 0
    if len(parts) > 1:
        try:
            off = int(parts[1].lstrip('#'), 0)
        except ValueError:
            return None
    return base, off


def main():
    for ver in (3150, 328):
        code = elf_code(ELF[ver])
        seq = decode(code)
        regs = {}          # reg -> (baseval, hold, lastwrite_idx, kind)
        access = collections.defaultdict(list)   # baseval -> [(addr, off, mn, ops, hold)]
        flashlit = collections.defaultdict(list)  # baseval -> [(addr, flashval)]
        calls = []
        for k, ins in enumerate(seq):
            # forget stale (distance > 40) — crude basic-block-ish approximation
            for r in [r for r, v in regs.items() if k - v[2] > 40]:
                del regs[r]
            lv = litval(ins, code)
            if lv is not None:
                # register written by the ldr: first operand
                dst = ins.op_str.split(',')[0].strip()
                regs[dst] = (lv, 0, k, 'lit')
                continue
            m = ins.mnemonic
            # add.w rX, rY, rZ, lsl #5   (stride 0x60)
            if m == 'add.w' and ins.op_str.endswith('lsl #5'):
                ops = [o.strip() for o in ins.op_str.split(',')]
                dst, s1, s2 = ops[0], ops[1], ops[2]
                if s1 in regs and regs[s1][3] == 'lit' and 0x20000000 <= regs[s1][0] < 0x20020000:
                    regs[dst] = (regs[s1][0], 0, k, 'blk')
                    continue
            # add.w rX, rY, #imm  / adds rX, rY, #imm  -> keep family with hold
            if m in ('add.w', 'adds', 'add') and ins.op_str.count(',') == 2:
                ops = [o.strip() for o in ins.op_str.split(',')]
                dst, s1, s2 = ops[0], ops[1], ops[2]
                if s1 in regs and regs[s1][3] == 'blk' and s2.startswith('#'):
                    try:
                        hold = int(s2.lstrip('#'), 0)
                    except ValueError:
                        hold = 0
                    regs[dst] = (regs[s1][0], regs[s1][1] + hold, k, 'blk')
                    continue
            # sub.w rX, rY, #imm
            if m in ('sub.w', 'subs', 'sub') and ins.op_str.count(',') == 2:
                ops = [o.strip() for o in ins.op_str.split(',')]
                if ops[1] in regs and regs[ops[1]][3] == 'blk' and ops[2].startswith('#'):
                    regs[ops[0]] = (regs[ops[1]][0], regs[ops[1]][1] - int(ops[2].lstrip('#'), 0), k, 'blk')
                    continue
            acc = memacc(ins)
            if acc:
                b, off = acc
                if b in regs and regs[b][3] == 'blk':
                    bv, hold, _, _ = regs[b]
                    access[bv].append((ins.address + SHIFT, off + hold, m, ins.op_str))
                continue
            if m in ('ldr', 'ldrb', 'ldrh') and '[pc' in ins.op_str and lv is not None \
               and 0x08020000 <= lv < 0x08080000:
                pass
            if m in ('bl', 'blx'):
                for r, v in regs.items():
                    if v[3] == 'blk':
                        calls.append((ins.address + SHIFT, r, v[0], v[1],
                                      ins.op_str))
                regs.clear()
                continue
            # any other write to a tracked reg kills it
            if m.startswith(('mov', 'movs', 'mov.w', 'ldr', 'pop', 'adr', 'mvn', 'lsl',
                             'lsr', 'and', 'orr', 'eor', 'bic', 'mul', 'mla', 'uxth',
                             'sxth', 'ubfx', 'sbfx', 'rsb', 'movw', 'movt', 'vldr')):
                dst = ins.op_str.split(',')[0].strip()
                if dst in regs:
                    del regs[dst]
        print("=" * 78)
        print("VERSION %s  instructions=%d" % (ver, len(seq)))
        print("-- 0x60-stride block bases and the offsets touched on them")
        for bv in sorted(access):
            hist = collections.Counter(o for _, o, _, _ in access[bv])
            sites = len(access[bv])
            top = " ".join("+0x%02X x%d" % (o, n) for o, n in sorted(hist.items())[:24])
            print("   0x%08X : %3d accesses | %s" % (bv, sites, top))
        print("-- accesses at +0x24..+0x38 (the H01.17-ish fields)")
        for bv in sorted(access):
            for a, o, mn, ops in access[bv]:
                if 0x20 <= o <= 0x3C:
                    print("   0x%08X base=0x%08X  +0x%02X  %-6s %s" % (a, bv, o, mn, ops))
        print("-- calls carrying a block pointer (candidate init/memcpy)")
        for a, r, bv, hold, ops in calls:
            print("   0x%08X  base=0x%08X (r%s +0x%X)  %s" % (a, bv, r, hold, ops))
    return 0


if __name__ == '__main__':
    sys.exit(main())
