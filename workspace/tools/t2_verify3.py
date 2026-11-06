# T2 stage 3: size the third addend [0x20003DB0+0x18] (read its writers) + store-count controls
import struct
from capstone import *
from capstone.arm import *

BASE = 0x08010000
DATA = {k: open(v, 'rb').read() for k, v in
        {'d8': r'data\servo_fw_samples\elf\v328d8.bin',
         '3150': r'data\servo_fw_samples\elf\v3150.bin'}.items()}
MD = Cs(CS_ARCH_ARM, CS_MODE_THUMB + CS_MODE_MCLASS + CS_MODE_LITTLE_ENDIAN)
MD.detail = True; MD.skipdata = True

def rd32(k, a):
    if a < BASE or a + 4 > BASE + len(DATA[k]):
        return None            # pool target outside the image: guard, not a false zero
    return struct.unpack_from('<I', DATA[k], a - BASE)[0]
def pcrel(it):
    return ((it.address + 4) & ~3) + it.operands[1].mem.disp

print("=== control: str.w ...,#0x234 store sites (must be exactly 1 per image) ===")
for k in DATA:
    n = 0
    for it in MD.disasm(DATA[k], BASE):
        if it.id == 0: continue
        if it.mnemonic.startswith('str') and len(it.operands) == 2 and \
           it.operands[1].type == ARM_OP_MEM and it.operands[1].mem.disp == 0x234:
            n += 1; print("   ", k, hex(it.address), it.mnemonic, it.op_str)
    print(f"   {k}: {n}")

print()
print("=== accesses to [0x20003DB0 + 0x18] in 3150: writers and readers ===")
k = '3150'
# collect sites where a reg holds base 0x20003DB0 via the pool (0x08024BB0)
pooladdr = None
for it in MD.disasm(DATA[k], BASE):
    if it.id and it.mnemonic.startswith('ldr') and len(it.operands) == 2 and \
       it.operands[1].type == ARM_OP_MEM and it.operands[1].mem.base == ARM_REG_PC:
        if rd32(k, pcrel(it)) == 0x20003DB0:
            pooladdr = pcrel(it)
print("   pool dword holding 0x20003DB0 @", hex(pooladdr))
# sites that load the pool (any register), then a +/-0x18 access to that register
base_loads = []
for it in MD.disasm(DATA[k], BASE):
    if it.id and it.mnemonic.startswith('ldr') and len(it.operands) == 2 and \
       it.operands[1].type == ARM_OP_MEM and it.operands[1].mem.base == ARM_REG_PC \
       and pcrel(it) == pooladdr:
        base_loads.append((it.address, it.operands[0].reg))
print("   base load sites:", [(hex(a), r) for a, r in base_loads])
for (a, reg) in base_loads:
    seq = list(MD.disasm(DATA[k][a + 4 - BASE: a + 4 - BASE + 40], a + 4))
    for j, it in enumerate(seq):
        if it.id and it.operands and it.operands[-1].type == ARM_OP_MEM and \
           it.operands[-1].mem.base == reg and it.operands[-1].mem.disp == 0x18:
            pre = " | ".join(f"{x.mnemonic} {x.op_str}" for x in seq[max(0, j - 6):j + 1])
            print(f"   @{hex(a)} .. {hex(it.address)}  {it.mnemonic} {it.op_str}\n        ctx: {pre}")

print()
print("=== 3150: what writes 0x20003DB0+8 (the subtrahend) ===")
for (a, reg) in base_loads:
    seq = list(MD.disasm(DATA[k][a + 4 - BASE: a + 4 - BASE + 44], a + 4))
    for j, it in enumerate(seq):
        if it.id and it.operands and it.operands[-1].type == ARM_OP_MEM and \
           it.operands[-1].mem.base == reg and it.operands[-1].mem.disp in (0, 4, 8):
            print(f"   @{hex(it.address)}  {it.mnemonic} {it.op_str}")
