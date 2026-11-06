"""mkelf.py - wrap a raw Cortex-M flash image (and its vendor FoE header) into a
proper ELF32 little-endian ARM file so standard tools (Ghidra, readelf, gdb)
accept it with the right addresses.

  * .text   at 0x08000000  = the flash image
  * .header at 0x00000000  = the vendor's 0x20-byte FoE header (non-alloc)
  * .symtab gets entry symbols (Reset/NMI/... from the vector table)

usage: python tools\\mkelf.py <firmware.bin> <out.elf>
"""
import sys, os, struct, time

FLASH_BASE = 0x08000000
VEC_NAMES = ['g_pfnVectors', 'Reset_Handler', 'NMI_Handler', 'HardFault_Handler',
             'MemManage_Handler', 'BusFault_Handler', 'UsageFault_Handler', '', '', '',
             '', 'SVC_Handler', 'DebugMon_Handler', '', 'PendSV_Handler', 'SysTick_Handler']


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no Cortex-M vector table in %s" % path)


def build(path, out_path):
    raw, hdr, flash = load(path)
    hdr_b = raw[:hdr]

    # ---- symbols from the vector table ----
    syms = []          # (name, value, size, info)
    for i, nm in enumerate(VEC_NAMES):
        if not nm or i == 0:
            continue
        v = struct.unpack_from('<I', flash, i * 4)[0]
        if v:
            syms.append((nm, v & ~1, 2, 0x12))       # STT_FUNC, GLOBAL
    syms.append(('g_flash_image', FLASH_BASE, len(flash), 0x11))   # STT_OBJECT
    syms.append(('g_sp_init', struct.unpack_from('<I', flash, 0)[0], 4, 0x11))

    # ---- layout ----
    # sections: [0]=NULL, [1]=.text(alloc), [2]=.header, [3]=.shstrtab, [4]=.symtab, [5]=.strtab
    text_off = 0x1000
    text_size = len(flash)
    hdr_off = (text_off + text_size + 3) & ~3
    hdr_size = len(hdr_b)
    shstr = b"\0.text\0.header\0.shstrtab\0.symtab\0.strtab\0"
    shstr_name = {}
    p = 1
    for s in ('.text', '.header', '.shstrtab', '.symtab', '.strtab'):
        shstr_name[s] = p
        p += len(s) + 1
    shstr_off = (hdr_off + hdr_size + 3) & ~3

    # strtab
    strtab = bytearray(b"\0")
    str_off = {}
    for nm, *_ in syms:
        str_off[nm] = len(strtab)
        strtab += nm.encode() + b"\0"
    strtab_off = (shstr_off + len(shstr) + 3) & ~3

    # symtab: NULL + shndx(1) + locals then globals
    nlocal = 1
    ng = len(syms)
    sym_ents = [struct.pack('<IIIBBH', 0, 0, 0, 0, 0, 0)]
    for nm, val, size, info in syms:
        sym_ents.append(struct.pack('<IIIBBH', str_off[nm], val, size, info, 0, 1))
    symtab = b"".join(sym_ents)
    symtab_off = (strtab_off + len(strtab) + 3) & ~3
    symtab_size = len(symtab)
    strtab_size = len(strtab)

    e_shoff = (symtab_off + symtab_size + 3) & ~3
    e_shnum = 6
    e_shstrndx = 3

    # ---- write ----
    buf = bytearray(e_shoff + e_shnum * 40)
    # ELF header
    struct.pack_into('<4s4B7x', buf, 0, b'\x7fELF', 1, 1, 1, 0)
    struct.pack_into('<HHIIIIIHHHHHH', buf, 16,
                     2,          # e_type = ET_EXEC
                     40,         # e_machine = EM_ARM
                     1,          # e_version
                     struct.unpack_from('<I', flash, 4)[0] & ~1,   # e_entry = Reset
                     0, e_shoff, 0x05000000,   # flags: EF_ARM_EABI_VER5
                     52, 32, 0, 40, e_shnum, e_shstrndx)

    def put(off, data):
        buf[off:off + len(data)] = data

    put(text_off, flash)
    put(hdr_off, hdr_b)
    put(shstr_off, shstr)
    put(symtab_off, symtab)
    put(strtab_off, strtab)

    def shdr(idx, name, typ, flags, addr, off, size, link=0, info=0, align=4, entsize=0):
        struct.pack_into('<IIIIIIIIII', buf, e_shoff + idx * 40,
                         name, typ, flags, addr, off, size, link, info, align, entsize)

    shdr(0, 0, 0, 0, 0, 0, 0)
    shdr(1, shstr_name['.text'], 1, 0x6, FLASH_BASE, text_off, text_size)          # PROGBITS|ALLOC|EXEC
    shdr(2, shstr_name['.header'], 1, 0x0, 0, hdr_off, hdr_size)
    shdr(3, shstr_name['.shstrtab'], 3, 0x0, 0, shstr_off, len(shstr), align=1)
    shdr(4, shstr_name['.symtab'], 2, 0x0, 0, symtab_off, symtab_size,
         link=5, info=nlocal, align=4, entsize=16)
    shdr(5, shstr_name['.strtab'], 3, 0x0, 0, strtab_off, strtab_size, align=1)

    open(out_path, 'wb').write(buf)
    print("%s -> %s" % (os.path.basename(path), out_path))
    print("   .text   0x%08x..0x%08x (%d B)" % (FLASH_BASE, FLASH_BASE + text_size, text_size))
    print("   entry   0x%08x" % (struct.unpack_from('<I', flash, 4)[0] & ~1))
    print("   .header %d B, %d symbols, %d B total" % (hdr_size, len(syms), len(buf)))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
