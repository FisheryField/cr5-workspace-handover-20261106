# T5e: verify the A-path source field bytes + readback-disassemble the candidate 1-byte patch
import struct
from capstone import *

BASE = r"D:\mydata\workspace\data\servo_fw_samples\elf"
FILES = {"D8": BASE + r"\v328d8.elf", "3150": BASE + r"\v3150.elf"}

def text_off(data, va):
    e_shoff = struct.unpack_from('<I', data, 0x20)[0]
    e_shentsize = struct.unpack_from('<H', data, 0x2E)[0]
    e_shnum = struct.unpack_from('<H', data, 0x30)[0]
    for i in range(e_shnum):
        o = e_shoff + i * e_shentsize
        name, typ, flags, addr, offset, size = struct.unpack_from('<IIIIII', data, o)
        if (flags & 0x4) and typ == 1 and addr <= va < addr + size:
            return offset + (va - addr)
    return None

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB); md.detail = True
SPOTS = {"3150": [0x0801F866, 0x0801F87C, 0x0801F98A, 0x0801F852], "D8": [0x08020C22, 0x08020C38, 0x08020D58]}
for tag, p in FILES.items():
    d = open(p, 'rb').read()
    for va in SPOTS[tag]:
        o = text_off(d, va)
        raw = d[o:o + 4]
        print("%s elfvaddr %08X (TRUE %08X) fileoff %X bytes=%s  -> %s" % (
            tag, va, va + 0x10000, o, raw.hex(),
            " | ".join("%X:%s %s" % (x.address, x.mnemonic, x.op_str) for x in md.disasm(raw, va))))

# candidate patch: 3150 TRUE 0x0802F866 / ELF 0x0801F866 : imm 0xa0 -> 0xa8
d = open(FILES["3150"], 'rb').read()
o = text_off(d, 0x0801F866)
raw = bytearray(d[o:o + 4])
print("\ncandidate patch 3150 ELF 0x0801F866 (TRUE 0x0802F866): before bytes", raw.hex())
for cand, nm in ((0xa8, "imm=0xa8"), (0xb0, "imm=0xb0")):
    r2 = bytearray(raw)
    r2[1] = cand          # imm12 low byte
    got = list(md.disasm(bytes(r2), 0x0801F866))
    print("  set byte[1]=%02X (%s) -> %s" % (cand, nm, " | ".join("%s %s" % (x.mnemonic, x.op_str) for x in got) or "UNDECODED"))
