#!/usr/bin/env python3
"""T3 step 8: correct true-address windows around +0x26 sites, both versions."""
import struct, sys

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


def decode(code, lo, hi):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    assert lo >= 0x08000000 and hi <= 0x08000000 + len(code), (hex(lo), hex(hi))
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


def win(code, true_addr, back, fwd, label):
    a = true_addr - SHIFT
    print("  ---- %s   (true 0x%08X)" % (label, true_addr))
    for i in decode(code, max(0x08000000, a - back), a + fwd):
        print("   %s true 0x%08X  %-9s %s" % (">>" if i.address == a else "  ",
                                              i.address + SHIFT, i.mnemonic, i.op_str))


def find26(code):
    out = []
    for ins in decode(code, 0x08000000, 0x08000000 + len(code)):
        op = ins.op_str
        if '[' in op and op[op.index('['):].endswith(']'):
            p = [x.strip() for x in op[op.index('[') + 1:-1].split(',')]
            if len(p) == 2:
                try:
                    if int(p[1].lstrip('#'), 0) == 0x26:
                        out.append((ins.address + SHIFT, ins.mnemonic, op))
                except ValueError:
                    pass
    return out


def main():
    for ver in (3150, 328):
        code = elf_code(ELF[ver])
        print("=" * 78)
        print("VERSION %s  -- every +0x26 access" % ver)
        for a, mn, op in find26(code):
            print("   true 0x%08X %-6s %s" % (a, mn, op))
    code = elf_code(ELF[3150])
    print("\n### 3150 windows")
    win(code, 0x0802148E, 0x50, 0x1C, "strh r3,[r5,#0x26] (block-A region)")
    win(code, 0x08018178, 0x40, 0x2C, "ldrh/strh +0x26 copy pair")
    win(code, 0x08013B04, 0x34, 0x14, "ldrh r4,[r0,#0x26]")
    return 0


if __name__ == '__main__':
    sys.exit(main())
