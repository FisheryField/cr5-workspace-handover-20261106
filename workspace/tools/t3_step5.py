#!/usr/bin/env python3
"""T3 step 5:
 (A) hunt the manufacturer default table for the H01.10..H01.19 group in flash
     (u16 LE 8,8,32,2,23,16,2500,90,100,1) - if it exists it is the "默认值"
     table and tells us where H01.17's default 90 lives.
 (B) direct scan of every memory access with immediate offset 0x26 / 0x32 /
     0x34 in both versions (offset census -> then read each site by hand).
 (C) scan for stores of the literal constant 90 (0x5a) into memory.
"""
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


def decode(code):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.skipdata = True
    return list(md.disasm(code, 0x08000000))


def main():
    seqs = {
        'H01.10..19 u16': struct.pack('<10H', 8, 8, 32, 2, 23, 16, 2500, 90, 100, 1),
        'H01.13..18 u16': struct.pack('<6H', 2, 23, 16, 2500, 90, 100),
        'H01.16..18 u16': struct.pack('<3H', 2500, 90, 100),
        'H01.14..18 u16': struct.pack('<5H', 23, 16, 2500, 90, 100),
    }
    for ver in (3150, 328):
        code = elf_code(ELF[ver])
        print("=" * 78)
        print("VERSION %s" % ver)
        print("-- (A) default-table hunt")
        for name, pat in seqs.items():
            offs = []
            i = code.find(pat)
            while i >= 0 and len(offs) < 6:
                offs.append(i)
                i = code.find(pat, i + 1)
            print("   %-16s len=%d -> %d hit(s) %s" % (
                name, len(pat), len(offs),
                " ".join("true 0x%08X" % (o + 0x08000000 + SHIFT) for o in offs)))

        print("-- (B) accesses with imm 0x26 / 0x32 / 0x34")
        for ins in decode(code):
            if ins.mnemonic.split('.')[0] not in (
                    'ldr', 'ldrb', 'ldrh', 'ldrsb', 'ldrsh', 'str', 'strb',
                    'strh', 'vldr', 'vstr', 'ldrd', 'strd'):
                continue
            op = ins.op_str
            if '[' not in op:
                continue
            mem = op[op.index('['):]
            if not mem.endswith(']'):
                continue
            parts = [p.strip() for p in mem[1:-1].split(',')]
            if len(parts) != 2:
                continue
            try:
                o = int(parts[1].lstrip('#'), 0)
            except ValueError:
                continue
            if o in (0x26, 0x32, 0x34):
                print("   true 0x%08X  %-6s %s" % (ins.address + SHIFT, ins.mnemonic, ins.op_str))

        print("-- (C) stores of constant 90 (0x5a) to memory")
        n = 0
        for k, ins in enumerate(decode(code)):
            if ins.mnemonic in ('movs', 'mov', 'mov.w') and ins.op_str.endswith('#0x5a'):
                reg = ins.op_str.split(',')[0].strip()
                for j in range(k + 1, min(k + 5, 1 << 30)):
                    nxt = seq_all = None
                    break
        # simpler: keep movs #0x5a sites and look ahead 3 instructions
        inst = decode(code)
        for k, ins in enumerate(inst):
            if ins.mnemonic in ('movs', 'mov', 'mov.w') and ins.op_str.endswith('#0x5a'):
                reg = ins.op_str.split(',')[0].strip()
                for j in range(k + 1, min(k + 4, len(inst))):
                    nx = inst[j]
                    if nx.mnemonic.startswith('str') and nx.op_str.startswith(reg + ',') \
                       and '[' in nx.op_str and 'sp' not in nx.op_str.split('[')[1][:4]:
                        print("   true 0x%08X  %-6s %s   <- %s #0x5a" % (
                            nx.address + SHIFT, nx.mnemonic, nx.op_str, ins.mnemonic))
                        n += 1
                        break
        print("   (%d store(s))" % n)
    return 0


if __name__ == '__main__':
    sys.exit(main())
