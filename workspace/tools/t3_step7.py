#!/usr/bin/env python3
"""T3 step 7 (corrected true addresses).

  * windows around the +0x26 sites, labelled with the provenance of the base reg
  * full read/write census on the 0x60-stride per-axis family, BOTH versions
  * asserts every requested address is a legal TRUE flash address
"""
import struct, sys, collections

ELF = {3150: r"D:\mydata\workspace\data\servo_fw_samples\elf\v3150.elf",
       328: r"D:\mydata\workspace\data\servo_fw_samples\elf\v328d8.elf"}
SHIFT = 0x10000


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


def decode_range(code, lo, hi):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    if lo < 0x08000000 or hi > 0x08000000 + len(code):
        raise SystemExit("window outside image: 0x%08X..0x%08X" % (lo, hi))
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.skipdata = True
    return list(md.disasm(code[lo - 0x08000000:hi - 0x08000000], lo))


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


def tracker(code, upto_lo, upto_hi):
    """forward walk over [upto_lo,upto_hi); returns list of (addr, baseval, off, mn, ops, held)"""
    out = []
    regs = {}
    for k, ins in enumerate(decode_range(code, upto_lo, upto_hi)):
        for r in [r for r, v in regs.items() if k - v[2] > 40]:
            del regs[r]
        lv = litval(ins, code)
        if lv is not None:
            regs[ins.op_str.split(',')[0].strip()] = (lv, 0, k, 'lit')
            continue
        m = ins.mnemonic
        if m == 'add.w' and ins.op_str.endswith('lsl #5'):
            o = [x.strip() for x in ins.op_str.split(',')]
            if o[1] in regs and regs[o[1]][3] == 'lit' and 0x20000000 <= regs[o[1]][0] < 0x20020000:
                regs[o[0]] = (regs[o[1]][0], 0, k, 'blk')
                continue
        if m in ('add.w', 'adds', 'add') and ins.op_str.count(',') == 2:
            o = [x.strip() for x in ins.op_str.split(',')]
            if o[1] in regs and regs[o[1]][3] == 'blk' and o[2].startswith('#'):
                regs[o[0]] = (regs[o[1]][0], regs[o[1]][1] + int(o[2].lstrip('#'), 0), k, 'blk')
                continue
        if m not in ('ldr', 'ldrb', 'ldrh', 'ldrsb', 'ldrsh', 'str', 'strb', 'strh',
                     'vldr', 'vstr', 'ldrd', 'strd') and '[' in ins.op_str:
            dst = ins.op_str.split(',')[0].strip()
            if dst in regs:
                del regs[dst]
        op = ins.op_str
        if '[' in op and op[op.index('['):].endswith(']'):
            parts = [p.strip() for p in op[op.index('[') + 1:-1].split(',')]
            if parts and parts[0] in regs and regs[parts[0]][3] == 'blk':
                off = 0
                if len(parts) > 1:
                    try:
                        off = int(parts[1].lstrip('#'), 0)
                    except ValueError:
                        off = 0
                bv, hold = regs[parts[0]][0], regs[parts[0]][1]
                out.append((ins.address + SHIFT, bv, off + hold, m, op))
    return out


def main():
    for ver in (3150, 328):
        code = elf_code(ELF[ver])
        print("=" * 78)
        print("VERSION %s" % ver)
        # full-image census: track in 4 KiB windows so provenance stays local
        allacc = []
        for win in range(0x08000000, 0x08000000 + len(code), 0x1000):
            allacc += tracker(code, win, min(win + 0x1000 + 0x40, 0x08000000 + len(code)))
        fam = [a for a in allacc if 0x20007300 <= a[1] < 0x20008000]
        bases = collections.Counter(a[1] for a in fam)
        print("  family bases used with stride 0x60:",
              {("0x%08X" % b): n for b, n in bases.items()})
        wr = [a for a in fam if a[3].startswith('str') or a[3].startswith('vstr')]
        rd = [a for a in fam if not (a[3].startswith('str') or a[3].startswith('vstr'))]
        print("  accesses: %d read / %d write" % (len(rd), len(wr)))
        hw = collections.Counter(a[2] for a in wr)
        print("  write offsets: " + " ".join("+0x%02X x%d" % (o, n) for o, n in sorted(hw.items())))
        print("  -- every WRITE site on the family")
        for a in wr:
            print("     true 0x%08X base=0x%08X +0x%02X  %-6s %s" % a)
        hr = collections.Counter(a[2] for a in rd)
        print("  read offsets: " + " ".join("+0x%02X x%d" % (o, n) for o, n in sorted(hr.items())))
    return 0


if __name__ == '__main__':
    sys.exit(main())
