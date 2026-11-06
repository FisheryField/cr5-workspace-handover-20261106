#!/usr/bin/env python3
"""T3 step 2:
 (1) pin the ELF<->true-address relation using the DOCUMENTED 3150 patch site
     0x08014AFE (bytes 2c 49 89 69 01 44) and the raw payload v3150.bin;
 (2) dump param.csv rows for H01.1x / H0C.0x;
 (3) find genuine literal-pool LOADS (ldr rX,[pc,#imm]) of candidate block
     addresses, with context.  Positive controls are included.
"""
import struct, sys, os

ELF = r"D:\mydata\workspace\data\servo_fw_samples\elf\v3150.elf"
BIN = r"D:\mydata\workspace\data\servo_fw_samples\elf\v3150.bin"
CSV = r"D:\mydata\workspace\data\official\servoCSV\param.csv"


def elf_code(path):
    d = open(path, 'rb').read()
    e_shoff, = struct.unpack_from('<I', d, 0x20)
    e_shentsize, e_shnum = struct.unpack_from('<HH', d, 0x2e)
    for i in range(e_shnum):
        o = e_shoff + i * e_shentsize
        sh_name, sh_type, sh_flags, sh_addr, sh_offset, sh_size = struct.unpack_from('<IIIIII', d, o)
        if sh_flags & 0x2 and sh_addr == 0x08000000:
            return d[sh_offset:sh_offset + sh_size], 0x08000000, sh_offset
    raise SystemExit("no alloc section at 0x08000000")


def find_vt(d):
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return base
    raise SystemExit("no vector table")


def main():
    code, base, elfoff = elf_code(ELF)
    print("ELF alloc section @0x%08X fileoff=0x%X size=0x%X" % (base, elfoff, len(code)))
    for a in (0x08014AFE, 0x08004AFE, 0x08024AFE):
        s = code[a - base:a - base + 8]
        print("  ELF vaddr 0x%08X bytes: %s" % (a, s.hex(' ')))

    d = open(BIN, 'rb').read()
    vt = find_vt(d)
    print("payload %s size=0x%X vector table at file offset 0x%X" % (os.path.basename(BIN), len(d), vt))
    for off in (0x4AFE, 0x4B1E, 0x4B1E - 0x20):
        if off + 8 <= len(d):
            print("  BIN file offset 0x%05X bytes: %s" % (off, d[off:off + 8].hex(' ')))

    print("\n-- param.csv")
    txt = open(CSV, 'rb').read().decode('gbk', 'replace').splitlines()
    print("lines=%d" % len(txt))
    for i, ln in enumerate(txt[:6]):
        print("  [%d] %s" % (i, ln[:180]))
    for ln in txt:
        if any(k in ln for k in ('H01.1', 'H0C.0', '编码器位置角', '校零', '编码器类型')):
            print("  *", ln.strip()[:240])

    # ---- literal-pool LOAD scan
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.skipdata = True

    loads = []
    for ins in md.disasm(code, base):
        if ins.mnemonic == 'ldr' and '[pc' in ins.op_str:
            try:
                off = int(ins.op_str.split('#')[-1].rstrip(']'), 0)
            except ValueError:
                continue
            tgt = ((ins.address + 4) & ~3) + off
            if base <= tgt <= base + len(code) - 4:
                loads.append((ins.address, struct.unpack_from('<I', code, tgt - base)[0]))
    print("\nliteral-pool loads decoded: %d" % len(loads))

    for lit in (0x200073A0, 0x2000129C, 0x20003DB0):
        hits = [(a, v) for a, v in loads if v == lit]
        print("\n### LOAD sites for 0x%08X : %d" % (lit, len(hits)))
        for a, _ in hits:
            lo = max(base, a - 0x30)
            print("  --- site 0x%08X  (context 0x%08X..)" % (a, lo))
            for ins in md.disasm(code[lo - base: a - base + 0x50], lo):
                mark = " >>" if ins.address == a else "   "
                print("  %s 0x%08X  %-8s %s" % (mark, ins.address, ins.mnemonic, ins.op_str))
    return 0


if __name__ == '__main__':
    sys.exit(main())
