# T2 stage 4: 3150 path-1 clamp bytes + function-pointer-table store hunt (both images)
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
    if a < BASE or a + 4 > BASE + len(DATA[k]): return None
    return struct.unpack_from('<I', DATA[k], a - BASE)[0]
def pcrel(it): return ((it.address + 4) & ~3) + it.operands[1].mem.disp

print("=== 3150 path-1 clamp (must mirror D8 0x080254C6..0x080254D4) ===")
for it in MD.disasm(DATA['3150'][0x08024986 - BASE: 0x080249A4 - BASE], 0x08024986):
    if it.id: print(f"{it.address:08x}  {it.bytes.hex(' '):<20} {it.mnemonic:<9} {it.op_str}")
    else: print(hex(it.address), "DATA", it.bytes.hex())

print()
print("=== pointer-table store hunt ===")
for k, tab in (('d8', 0x20000078), ('3150', 0x20000074)):
    loads = [(it.address, it.operands[0].reg) for it in MD.disasm(DATA[k], BASE)
             if it.id and it.mnemonic.startswith('ldr') and len(it.operands) == 2 and
             it.operands[1].type == ARM_OP_MEM and it.operands[1].mem.base == ARM_REG_PC and
             rd32(k, pcrel(it)) == tab]
    print(f"{k}: table {hex(tab)} load sites = {len(loads)}")
    stores = 0
    for (a, reg) in loads:
        for j in MD.disasm(DATA[k][a + 4 - BASE: a + 4 - BASE + 32], a + 4):
            if j.id and j.mnemonic.startswith('str') and j.operands and \
               j.operands[-1].type == ARM_OP_MEM and j.operands[-1].mem.base == reg:
                stores += 1
                print("   STORE after base load:", hex(j.address), j.mnemonic, j.op_str, "(base load @", hex(a), ")")
    # direct store to the table address range with any base reg holding it via add/sub
    direct = 0
    for it in MD.disasm(DATA[k], BASE):
        if it.id and it.mnemonic.startswith('str') and len(it.operands) == 2 and \
           it.operands[1].type == ARM_OP_MEM and it.operands[1].mem.base == ARM_REG_PC:
            direct += 1     # nothing meaningful; kept as a sanity counter
    print(f"   stores via table base register: {stores}   (str with [pc,...] base: {direct})")
