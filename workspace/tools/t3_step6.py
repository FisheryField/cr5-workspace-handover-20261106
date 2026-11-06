#!/usr/bin/env python3
"""T3 step 6: window dumps (true-address labelling) + who writes +0x26 with what."""
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
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.skipdata = True
    return list(md.disasm(code[lo - 0x08000000:hi - 0x08000000], lo))


def win(code, true_addr, back, fwd, label):
    a = true_addr - SHIFT
    print("  ---- %s  (true 0x%08X / elf 0x%08X)" % (label, true_addr, a))
    seq = decode(code, max(0x08000000, a - back), a + fwd)
    for i in seq:
        mark = ">>" if i.address == a else "  "
        print("   %s true 0x%08X  %-9s %s" % (mark, i.address + SHIFT, i.mnemonic, i.op_str))


def main():
    code = elf_code(ELF[3150])
    print("### 3150")
    win(code, 0x0801148E, 0x40, 0x30, "strh r3,[r5,#0x26]")
    win(code, 0x08008178, 0x40, 0x40, "ldrh/strh +0x26 pair")
    win(code, 0x08013B04, 0x30, 0x18, "ldrh r4,[r0,#0x26] A")
    win(code, 0x080185C4, 0x30, 0x18, "ldrh r4,[r0,#0x26] B")
    win(code, 0x0801436C, 0x30, 0x14, "call with block-A ptr")
    win(code, 0x0801C09E, 0x30, 0x14, "call with block-A ptr (2)")

    # who stores a constant into a +0x26 field, and with what value?
    print("### 3150: instructions loading constant 38 (0x26) right before a store")
    inst = decode(code, 0x08000000, 0x08000000 + len(code))
    for k, i in enumerate(inst):
        if i.mnemonic in ('movs', 'mov', 'mov.w') and i.op_str.split(',')[-1].strip() in ('#0x26', '#38'):
            reg = i.op_str.split(',')[0].strip()
            for j in range(k + 1, min(k + 6, len(inst))):
                nx = inst[j]
                if nx.op_str.startswith(reg + ',') and '[' in nx.op_str:
                    print("   true 0x%08X  %-6s %-28s <- 0x26" % (
                        nx.address + SHIFT, nx.mnemonic, nx.op_str))
                    break
    return 0


if __name__ == '__main__':
    sys.exit(main())
