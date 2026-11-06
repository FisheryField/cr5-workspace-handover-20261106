# T2 stage 2: constants/sign audit + third-addend + function-pointer table hunt
import struct
from capstone import *
from capstone.arm import *

BASE = 0x08010000
BIN = {'d8': r'data\servo_fw_samples\elf\v328d8.bin',
       '3150': r'data\servo_fw_samples\elf\v3150.bin'}
DATA = {k: open(v, 'rb').read() for k, v in BIN.items()}
MD = Cs(CS_ARCH_ARM, CS_MODE_THUMB + CS_MODE_MCLASS + CS_MODE_LITTLE_ENDIAN)
MD.detail = True
MD.skipdata = True

def rd32(k, a):
    if a < BASE or a + 4 > BASE + len(DATA[k]):
        return None
    return struct.unpack_from('<I', DATA[k], a - BASE)[0]

def rd64(k, a):
    return struct.unpack_from('<Q', DATA[k], a - BASE)[0]

def pcrel(it):
    return ((it.address + 4) & ~3) + it.operands[1].mem.disp

print("=== DEBUG: operand form of PC-relative load (positive control) ===")
for it in MD.disasm(DATA['3150'][0x08024AFE - BASE: 0x08024B06 - BASE], 0x08024AFE):
    if it.id == 0:
        print(hex(it.address), "DATA", it.bytes.hex()); continue
    ops = [(o.type, (o.mem.base, o.mem.disp) if o.type == ARM_OP_MEM else None) for o in it.operands]
    pv = pcrel(it) if it.operands[1].type == ARM_OP_MEM and it.operands[1].mem.base == ARM_REG_PC else None
    print(hex(it.address), it.mnemonic, it.op_str, "| ops:", ops,
          "| pcrel ->", hex(pv) if pv else '-', "| dword =", hex(rd32('3150', pv) or 0) if pv else '-')
assert rd32('3150', 0x08024BB0) == 0x20003DB0, "POSITIVE CONTROL FAILED"

def ram_pool_bases(k):
    """all PC-relative loads whose pool dword is a RAM global"""
    out = []
    for it in MD.disasm(DATA[k], BASE):
        if it.mnemonic.startswith('ldr') and len(it.operands) == 2 and \
           it.operands[1].type == ARM_OP_MEM and it.operands[1].mem.base == ARM_REG_PC:
            v = rd32(k, pcrel(it))
            if v is not None and 0x20000000 <= v < 0x20020000:
                out.append((it.address, v, it.operands[0].reg))
    return out

print()
print("=== third-addend scan: ldr rB,=<global> ; ... ; ldr rB,[rB,#0x18] ; add ===")
for k in DATA:
    rp = ram_pool_bases(k)
    hits = []
    for (a, v, reg) in rp:
        for j in MD.disasm(DATA[k][a + 4 - BASE: a + 4 - BASE + 36], a + 4):
            if j.mnemonic.startswith('ldr') and len(j.operands) == 2 and \
               j.operands[1].type == ARM_OP_MEM and j.operands[1].mem.base == reg and \
               j.operands[1].mem.disp == 0x18:
                nxt = next(MD.disasm(DATA[k][j.address + j.size - BASE:
                                             j.address + j.size - BASE + 4], j.address + j.size), None)
                hits.append((a, v, j.address, nxt.mnemonic if nxt else '?'))
                break
    print(f"{k}: RAM pool bases={len(rp)}  [base+0x18] loads={len(hits)}")
    for h in hits:
        print("   ", hex(h[0]), "base=", hex(h[1]), "ldr@", hex(h[2]), "next:", h[3])
    assert k != '3150' or any(h[2] == 0x08024B00 for h in hits), "POSITIVE CONTROL FAILED: 3150 known site 0x08024B00 missing"

print()
print("=== 0.5 constants: hardware single-precision vmov.f32 sN,#0.5 sites ===")
for k in DATA:
    print("--", k)
    for it in MD.disasm(DATA[k], BASE):
        if it.mnemonic.startswith('vmov') and 'f32' in it.op_str and '5.000000e-01' in it.op_str:
            print("   ", hex(it.address), it.mnemonic, it.op_str)
            for j in MD.disasm(DATA[k][it.address + it.size - BASE:
                                      it.address + it.size - BASE + 16], it.address + it.size):
                print("        +", hex(j.address), j.mnemonic, j.op_str)

print()
print("=== 0.5 constants: double 0.5 / -0.5 in literal pools + who loads them ===")
for k in DATA:
    d = DATA[k]
    for pat, name in ((0x3FE0000000000000, 'double +0.5'), (0xBFE0000000000000, 'double -0.5')):
        addrs = []
        for off in range(0, len(d) - 8, 4):
            if struct.unpack_from('<Q', d, off)[0] == pat:
                addrs.append(BASE + off)
        loaders = []
        for it in MD.disasm(d, BASE):
            if it.mnemonic.startswith('vldr') and len(it.operands) == 2 and \
               it.operands[1].type == ARM_OP_MEM and it.operands[1].mem.base == ARM_REG_PC:
                if pcrel(it) in addrs:
                    loaders.append(it.address)
        print(f"{k}: {name} pool sites={[hex(a) for a in addrs]} loaders={[hex(a) for a in loaders]}")

print()
print("=== function pointer table [0x20000078]/[0x20000074] ===")
for k, addr in (('d8', 0x20000078), ('3150', 0x20000074)):
    d = DATA[k]
    refs = [a for (a, v, r) in ram_pool_bases(k) if v == addr]
    print(k, hex(addr), "pool refs:", len(refs), [hex(r) for r in refs])
    # any store into [reg+8]/[reg] where reg holds that base?
    for r in refs:
        seq = list(MD.disasm(d[r - BASE: r - BASE + 48], r))
        print("    @", hex(r), " | ".join(f"{j.mnemonic} {j.op_str}" for j in seq[:10]))

print()
print("=== extra dumps ===")
for k, s, n in (('d8', 0x080254A0, 0x80), ('3150', 0x08024940, 0x62)):
    print(f"--- {k} @{s:#x} ---")
    for it in MD.disasm(DATA[k][s - BASE: s - BASE + n], s):
        print(f"{it.address:08x}  {it.bytes.hex(' '):<20} {it.mnemonic:<9} {it.op_str}")
