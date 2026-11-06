# T2 independent verification: +0x234 construction in 3.2.D.8 vs 3.1.5.0
# true flash addr = 0x08010000 + file offset
import struct, sys
from capstone import *
from capstone.arm import *

BASE = 0x08010000
BIN = {'d8': r'data\servo_fw_samples\elf\v328d8.bin',
       '3150': r'data\servo_fw_samples\elf\v3150.bin'}
DATA = {k: open(v, 'rb').read() for k, v in BIN.items()}
MD = Cs(CS_ARCH_ARM, CS_MODE_THUMB + CS_MODE_MCLASS + CS_MODE_LITTLE_ENDIAN)
MD.detail = True
MD.skipdata = True   # CRITICAL: without this the linear sweep stops at the first
                     # undecodable byte -> silent empty results (caught by the
                     # movw #0x4e20 positive control returning 0 sites)

def rd32(k, addr):
    return struct.unpack_from('<I', DATA[k], addr - BASE)[0]

def dis(k, start, nbytes, label=''):
    print(f"--- {k} {label} @{start:#010x} ({nbytes} B) ---")
    code = DATA[k][start - BASE: start - BASE + nbytes]
    for i in MD.disasm(code, start):
        print(f"{i.address:08x}  {i.bytes.hex(' '):<20} {i.mnemonic:<9} {i.op_str}")

def poolval(k, addr, it):
    # PC-relative literal: ((addr+4)&~3) + imm  (imm lives in mem.disp for ldr rX,[pc,#imm])
    pc = (it.address + 4) & ~3
    imm = it.operands[1].mem.disp
    return pc + imm

print("=== POSITIVE CONTROLS ===")
for k in DATA:
    d = DATA[k]
    print(k, "size", len(d), "SP", hex(rd32(k, BASE)), "Reset", hex(rd32(k, BASE + 4)))
    for s, tag in ((b'DS.3.1.5.0', 'v3150'), (b'DS.3.2.D.8', 'v32D8')):
        print("   ", tag, hex(BASE + d.find(s)) if d.find(s) >= 0 else "NOT FOUND")
    # movw #0x4e20 (20000) scan with skipdata linear sweep
    hits = []
    for it in MD.disasm(d, BASE):
        if it.mnemonic == 'movw':
            ops = [o for o in it.operands if o.type == ARM_OP_IMM]
            if ops and ops[0].imm == 0x4e20:
                hits.append(it.address)
    print("    movw #0x4e20 sites:", [hex(h) for h in hits])

print()
print("=== CHAIN DUMPS ===")
dis('d8', 0x08025520, 0x100, 'D8 core formula')
dis('d8', 0x080255E0, 0x30, 'D8 +0x234 -> +0x238')
dis('3150', 0x080249A0, 0x70, '3150 rounding')
dis('3150', 0x08024A10, 0xE8, '3150 branches before +0x234')
dis('3150', 0x08024B30, 0x40, '3150 +0x238 tail')

print()
print("=== [base+0x18] third-addend pattern (pool base -> ldr [base+0x18]) ===")
for k in DATA:
    d = DATA[k]
    sites = []
    for it in MD.disasm(d, BASE):
        if it.mnemonic.startswith('ldr') and len(it.operands) == 2 and \
           it.operands[1].type == ARM_OP_MEM and it.operands[1].mem.base == ARM_REG_PC:
            v = poolval(k, it.address, it)
            sites.append((it.address, v, it.operands[0].reg))
    ram = [s for s in sites if (s[1] & 0xFFF00000) == 0x20000000]
    found = []
    for (a, v, reg) in ram:
        for j in MD.disasm(d[a + 4 - BASE: a + 4 - BASE + 32], a + 4):
            if j.mnemonic.startswith('ldr') and len(j.operands) == 2 and \
               j.operands[1].type == ARM_OP_MEM and j.operands[1].mem.base == reg \
               and j.operands[1].mem.disp == 0x18:
                found.append((a, v, j.address))
                break
    print(k, "PC-rel pool loads:", len(sites), " RAM-targeted:", len(ram),
          " ->[base+0x18] loads:", len(found))
    for f in found:
        print("    ", hex(f[0]), "base=", hex(f[1]), "ldr@", hex(f[2]))

print()
print("=== function-pointer-table refs ===")
for k, addr in (('d8', 0x20000078), ('3150', 0x20000074)):
    d = DATA[k]
    refs = []
    for it in MD.disasm(d, BASE):
        if it.mnemonic.startswith('ldr') and len(it.operands) == 2 and \
           it.operands[1].type == ARM_OP_MEM and it.operands[1].mem.base == ARM_REG_PC:
            if poolval(k, it.address, it) == addr:
                refs.append(it.address)
    print(k, hex(addr), "pool refs:", len(refs), [hex(r) for r in refs])
    for r in refs[:6]:
        code = d[r - BASE: r - BASE + 40]
        outs = []
        for j in MD.disasm(code, r):
            outs.append(f"{j.mnemonic} {j.op_str}")
            if j.mnemonic.startswith('bl'):
                break
        print("    @", hex(r), " | ".join(outs))
