# -*- coding: utf-8 -*-
"""T3: hunt the per-axis parameter block 0x200073A0 + axis*0x60 in v3150.
Address convention check + literal-pool scan + windowed disassembly.
Positive controls included (must never return silently empty).
"""
import struct, sys
from capstone import *

ELF = r"D:\mydata\workspace\data\servo_fw_samples\elf\v3150.elf"
raw = open(ELF, 'rb').read()
print("file size", len(raw))

# ---- ELF program headers
assert raw[:4] == b'\x7fELF'
e_phoff = struct.unpack_from('<I', raw, 0x1c)[0]
e_phentsize = struct.unpack_from('<H', raw, 0x2a)[0]
e_phnum = struct.unpack_from('<H', raw, 0x2c)[0]
e_shoff = struct.unpack_from('<I', raw, 0x20)[0]
e_shentsize = struct.unpack_from('<H', raw, 0x2e)[0]
e_shnum = struct.unpack_from('<H', raw, 0x30)[0]
segs = []
for i in range(e_phnum):
    o = e_phoff + i * e_phentsize
    p_type, p_off, p_va, p_pa, p_fsz, p_msz, p_fl, p_al = struct.unpack_from('<IIIIIIII', raw, o)
    if p_type == 1:
        segs.append((p_off, p_va, p_fsz))
    print("PH %d type=%x off=%x va=%x filesz=%x memsz=%x fl=%x" % (i, p_type, p_off, p_va, p_fsz, p_msz, p_fl))
for i in range(e_shnum):
    o = e_shoff + i * e_shentsize
    nm, typ, fl, addr, off, size = struct.unpack_from('<IIIIII', raw, o)[:6]
    print("SH %d name=%x type=%x addr=%x off=%x size=%x" % (i, nm, typ, addr, off, size))
names = raw[e_shoff + struct.unpack_from('<H', raw, e_shoff + 0x28)[0]:]
# section name strings
ns_off = struct.unpack_from('<I', raw, e_shoff + 0x10)[0] if e_shnum else 0
print("shstrtab off=%x" % ns_off)


def fo2va(off):
    for p_off, p_va, p_fsz in segs:
        if p_off <= off < p_off + p_fsz:
            return p_va + (off - p_off)
    return None


def va2fo(va):
    for p_off, p_va, p_fsz in segs:
        if p_va <= va < p_va + p_fsz:
            return p_off + (va - p_va)
    return None


def rd(va, n):
    fo = va2fo(va)
    if fo is None:
        return None
    return raw[fo:fo + n]


# ---- POSITIVE CONTROL 1: address convention. version string should be at true flash 0x08027DCF
for va in (0x08027DCF, 0x08017DCF):
    s = rd(va, 16)
    print("PC1 str @%08x = %r" % (va, s))

# ---- POSITIVE CONTROL 2: known RAM globals as literal-pool dwords
CTRL = [0x2000129C, 0x20003DB0, 0x20000074, 0x20000078]
for c in CTRL:
    pat = struct.pack('<I', c)
    hits = []
    st = 0
    while True:
        k = raw.find(pat, st)
        if k < 0:
            break
        hits.append(fo2va(k))
        st = k + 1
    print("PC2 literal %08x -> %d hits %s" % (c, len(hits), [hex(h) if h else None for h in hits][:12]))

# ---- main scan: literal-pool dwords pointing into 0x20007000..0x20007A00
lo, hi = 0x20007000, 0x20007A00
found = {}
for off in range(0, len(raw) - 4 + 1, 1):
    v = struct.unpack_from('<I', raw, off)[0]
    if lo <= v < hi:
        va = fo2va(off)
        if va is not None:
            found.setdefault(v, []).append(va)
for v in sorted(found):
    print("LIT %08x -> %s" % (v, [hex(x) for x in found[v]]))

# ---- adjacent-window search: any literal dword in 0x20007000..0x20009000 (broader, count only)
cnt = 0
for off in range(0, len(raw) - 4 + 1, 4):
    v = struct.unpack_from('<I', raw, off)[0]
    if 0x20006000 <= v < 0x20009000:
        cnt += 1
print("broad count 0x20006000..0x20009000 (4-aligned) =", cnt)

# ---- disasm windows around each hit
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
md.detail = False
for v in sorted(found):
    for h in found[v]:
        start = h - 0x60
        code = rd(start, 0x60 + 0x40)
        if code is None:
            continue
        print("=== window @%08x (hit %08x = %08x)" % (start, h, v))
        for ins in md.disasm(code, start):
            mark = "  <== LIT" if ins.address == h else ""
            print("  %08x  %-8s %s%s" % (ins.address, ins.bytes.hex(), ins.mnemonic, " " + ins.op_str + mark))
