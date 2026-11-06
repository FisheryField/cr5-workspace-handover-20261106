#!/usr/bin/env python3
"""T3 step 3: census the per-axis 0x60-stride block.

For each version:
  * find literal-pool loads of the block base (found analytically as the base
    used by `add.w rX, rBase, rAxisTimes3, lsl #5`)
  * dump every memory access with offset in 0x20..0x40 in those functions,
    plus the immediate constants involved
  * structural comparison of D8 vs 3150 (strides only, never absolute addrs)
"""
import struct, sys

ELF = {3150: r"D:\mydata\workspace\data\servo_fw_samples\elf\v3150.elf",
       328: r"D:\mydata\workspace\data\servo_fw_samples\elf\v328d8.elf"}


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


def insns(code):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.skipdata = True
    return list(md.disasm(code, 0x08000000))


def litload(ins, code):
    if ins.mnemonic in ('ldr', 'ldr.w') and '[pc' in ins.op_str:
        try:
            off = int(ins.op_str.split('#')[-1].rstrip(']'), 0)
        except ValueError:
            return None
        t = ((ins.address + 4) & ~3) + off
        if 0x08000000 <= t <= 0x08000000 + len(code) - 4:
            return struct.unpack_from('<I', code, t - 0x08000000)[0]
    return None


def main():
    for ver, path in ELF.items():
        code = elf_code(path)
        seq = insns(code)
        print("=" * 78)
        print("VERSION %s  (%s), %d instructions" % (ver, path.split('\\')[-1], len(seq)))

        # map address -> index for context windows
        idx = {i.address: k for k, i in enumerate(seq)}

        # ---- structural: find `add.w rX, rB, rA, lsl #5` preceded at most 6
        #      instructions back by a literal-pool load of the base.
        cands = []
        for k, i in enumerate(seq):
            if i.mnemonic == 'add.w' and i.op_str.endswith('lsl #5'):
                for j in range(max(0, k - 8), k):
                    v = litload(seq[j], code)
                    if v is not None and 0x20000000 <= v < 0x20040000:
                        cands.append((i.address, seq[j].address, v, i.op_str, j))
                        break
        # group by base value
        bases = {}
        for a, la, v, ops, j in cands:
            bases.setdefault(v, []).append((a, la, ops, j))
        print("  RAM literal bases feeding '...,lsl #5' adds:")
        for v, lst in sorted(bases.items()):
            print("    0x%08X : %d site(s)" % (v, len(lst)))
            for a, la, ops, j in lst[:10]:
                print("        site 0x%08X (lit loaded @0x%08X)  %s" % (a, la, ops))

        for TARGET in sorted(bases):
            sites = bases[TARGET]
            print("\n  #### deep dump for base 0x%08X (%d sites)" % (TARGET, len(sites)))
            for a, la, ops, j in sites:
                lo = max(0, j - 14)
                hi = min(len(seq), j + 34)
                print("   -- function window around 0x%08X" % a)
                for k in range(lo, hi):
                    s = seq[k]
                    star = ">>" if s.address == a else "  "
                    print("   %s 0x%08X  %-9s %s" % (star, s.address, s.mnemonic, s.op_str))
    return 0


if __name__ == '__main__':
    sys.exit(main())
