"""Scan both servo ELFs for instructions touching the 0x607A field offset (+0x24C)
and neighbours.  Address convention (verified against known version strings):
    ELF .text vaddr (== Ghidra project coordinate)
    TRUE flash address = vaddr + 0x10000      (== 0x08010000 + payload file offset)
"""
import struct, json
from capstone import *
from capstone.arm import *

ELF = {
    'v328d8': r'D:\mydata\workspace\data\servo_fw_samples\elf\v328d8.elf',
    'v3150':  r'D:\mydata\workspace\data\servo_fw_samples\elf\v3150.elf',
}
TARGETS = [0x24c, 0x238, 0x234, 0x230, 0x22c, 0x20c, 0x1ae, 0x1af, 0x2a4,
           0x31f, 0x30, 0x14, 0x1c, 0xa8, 0xb0, 0x36, 0xba, 0xa2,
           0x234, 0x10, 0x18, 0x04, 0x0c, 0x20]

def load(path):
    d = open(path, 'rb').read()
    shoff, shnum, shstr = struct.unpack_from('<I', d, 0x20)[0], struct.unpack_from('<H', d, 0x30)[0], struct.unpack_from('<H', d, 0x32)[0]
    def sh(i):
        return struct.unpack_from('<10I', d, shoff + i * 40)
    st = sh(shstr)
    names = {}
    for i in range(shnum):
        s = sh(i)
        e = d.index(b'\x00', st[4] + s[0])
        names[d[st[4] + s[0]:e].decode()] = s
    return d, names

def scan(d, names):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB); md.detail = True
    md.skipdata = True   # without this capstone stops at the first undecodable byte

    s = names['.text']
    code = d[s[4]:s[4] + s[5]]
    mem = {t: [] for t in TARGETS}; imm = {t: [] for t in TARGETS}
    n = 0
    for insn in md.disasm(code, s[3]):
        n += 1
        if insn.id == 0:      # skipdata pseudo-instruction (.byte)
            continue
        for op in insn.operands:
            if op.type == ARM_OP_MEM and op.mem.disp in mem:
                mem[op.mem.disp].append((insn.address, insn.mnemonic, insn.op_str, insn.bytes.hex()))
            elif op.type == ARM_OP_IMM and op.imm in imm:
                imm[op.imm].append((insn.address, insn.mnemonic, insn.op_str, insn.bytes.hex()))
    return n, mem, imm

PC = {  # positive controls: (imm value, expected ghidra addr per SERVO_SUMMARY)
    'v328d8': (0x4e20, 0x080155A6),
    'v3150':  (0x4e20, 0x08019248),
}
res = {}
for name, path in ELF.items():
    d, names = load(path)
    n, mem, imm = scan(d, names)
    print('=' * 72)
    print(name, 'text', hex(names['.text'][3]), hex(names['.text'][5]), 'insns', n)
    # positive control 1: known movw #0x4e20 site
    v, want = PC[name]
    sites = [a for a, m, o, b in imm.get(v, []) if m.startswith('movw')]
    print('  POSCTL movw #0x%x sites (ghidra)=%s  want %08x  %s'
          % (v, [hex(x) for x in sites], want, 'PASS' if want in sites else 'FAIL'))
    print('  POSCTL mem[+0x31f] count=%d  mem[+0x238] count=%d  mem[+0x1af] count=%d'
          % (len(mem[0x31f]), len(mem[0x238]), len(mem[0x1af])))
    print('  (positive controls must be non-zero, else scanner is silently broken)')
    for t in sorted(set(TARGETS)):
        print('    [+0x%03x] mem=%-3d imm=%-3d' % (t, len(mem[t]), len(imm[t])))
    for t in (0x24c, 0x238, 0x230):
        for kind, tab in (('MEM', mem), ('IMM', imm)):
            if tab[t]:
                print('  --- +0x%03x %s ---' % (t, kind))
                for a, m, o, b in tab[t]:
                    print('    ghidra=%08x true=%08x  %-9s %-26s %s' % (a, a + 0x10000, m, o, b))
    res[name] = dict(n=n, mem={hex(k): v for k, v in mem.items()}, imm={hex(k): v for k, v in imm.items()})
json.dump(res, open(r'D:\mydata\workspace\tools\z_607a_scan.json', 'w'), indent=1)
print('json written')
