"""servo_t4_dump.py - bounded disassembly dumper for the servo payloads.

Addresses are given in ELF/payload coordinates (payload loaded at 0x08000000);
TRUE flash address = ELF address + 0x10000  (payload base is really 0x08010000,
proof: payload word1 = reset vector 0x0801019d).

usage:
  python tools\\servo_t4_dump.py <payload.bin> 0x08015602:40 0x08014b62:20
  python tools\\servo_t4_dump.py <payload.bin> --grep 0x238,0x24c,0x230
  python tools\\servo_t4_dump.py <payload.bin> --handlers          # movw #0x329 stub table
"""
import sys, re


def main(argv):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)

    path = argv[0]
    d = open(path, 'rb').read()
    # locate vector table (payload start)
    import struct
    start = 0
    for b in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, b)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            start = b
            break
    code = d[start:]
    print("== %s payload=%d B, code starts at file off 0x%x" % (path, len(d), start))

    HARD = 4000000  # instruction cap, hard bound against decode-stall loops

    def dis_all():
        out = []
        a = 0
        guard = 0
        while a <= len(code) - 2 and guard < HARD:
            guard += 1
            ms = list(md.disasm(code[a:a + 4], 0x08000000 + a))
            if not ms:
                a += 2
                continue
            i = ms[0]
            out.append((a, i.address, i.mnemonic, i.op_str, i.size))
            a += i.size
        return out

    if '--handlers' in argv:
        insns = dis_all()
        lit = {}
        for off, a, m, o, s in insns:
            if m == 'ldr' and 'pc' in o.split(',')[1:2][0] if ',' in o else False:
                pass
        # resolve literal-pool dwords for base identification
        litmap = {}
        for off, a, m, o, s in insns:
            if m == 'ldr' and '[pc' in o:
                mm = re.search(r'#(0x[0-9a-f]+)', o)
                if mm:
                    tgt = ((a + 4) & ~3) + int(mm.group(1), 16)
                    fo = tgt - 0x08000000
                    if 0 <= fo <= len(code) - 4:
                        litmap[a] = struct.unpack_from('<I', code, fo)[0]
        n = 0
        for k, (off, a, m, o, s) in enumerate(insns):
            if m == 'movw' and re.search(r'#0x329\b', o):
                base = None
                for j in range(k, min(len(insns), k + 8)):
                    if insns[j][1] in litmap:
                        base = litmap[insns[j][1]]
                    mm = re.search(r'#(0x[0-9a-f]+)\b', insns[j][3])
                    if insns[j][2] in ('addw', 'add.w', 'add') and 'r3' in insns[j][3] and mm:
                        pass
                mm2 = re.search(r'#(0x[0-9a-f]+)\b', o)
                print("   movw#0x329 @0x%08x (true 0x%08x)  base=0x%08x  %s" %
                      (a, a + 0x10000, base or 0, o))
                n += 1
        print("   total movw #0x329 sites: %d" % n)
        return 0

    if '--grep' in argv:
        vals = [int(x, 16) for x in argv[argv.index('--grep') + 1].split(',')]
        insns = dis_all()
        print("   instructions decoded: %d" % len(insns))
        for v in vals:
            pats = ['#0x%x' % v, '#%d' % v]
            hits = [(a, m, o) for _, a, m, o, _ in insns if any(p in o for p in pats)]
            # classify: pc/sp-relative immediates are literal-pool / stack offsets,
            # NOT struct-field offsets -> they must not be counted as field accesses.
            real, other = [], []
            for a, m, o in hits:
                body = o[o.index('[') + 1:] if '[' in o else o
                isoff = ('[pc' in o) or ('[sp' in o) or ('ldr' in m and 'pc' in o)
                (other if isoff else real).append((a, m, o))
            print("   imm 0x%-6x -> %d site(s) total; %d non-pc/sp, %d pc/sp-relative(FP)" %
                  (v, len(hits), len(real), len(other)))
            for a, m, o in real:
                print("       REAL? 0x%08x / true 0x%08x  %-9s %s" % (a, a + 0x10000, m, o))
            for a, m, o in other:
                print("       fp    0x%08x / true 0x%08x  %-9s %s" % (a, a + 0x10000, m, o))
        return 0

    for spec in argv[1:]:
        addr_s, _, n_s = spec.partition(':')
        addr = int(addr_s, 16)
        n = int(n_s) if n_s else 25
        a = addr - 0x08000000
        print("--- dump @ ELF 0x%08x  (true 0x%08x)  %d insn" % (addr, addr + 0x10000, n))
        c = 0
        while c < n and a <= len(code) - 2:
            ms = list(md.disasm(code[a:a + 4], 0x08000000 + a))
            if not ms:
                a += 2
                print("  0x%08x (true 0x%08x)  ??? .hword 0x%04x" %
                      (0x08000000 + a, 0x08010000 + a, struct.unpack_from('<H', code, a)[0]))
                continue
            i = ms[0]
            print("  0x%08x (true 0x%08x)  %-10s %s" % (i.address, i.address + 0x10000, i.mnemonic, i.op_str))
            a += i.size
            c += 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
