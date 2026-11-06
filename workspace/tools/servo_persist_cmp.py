"""servo_persist_cmp.py - compare the non-volatile storage routines of the two
Dobot servo firmware versions.

Established with tools/servo_flash_hunt.py:

  v3.2.D.8  STM32F4 flash HAL: unlock @0x080044ec (keys 0x45670123/0xCDEF89AB)
            its ONLY caller @0x08001862 is the save routine:
              - 0x18 (24) byte record built on the stack
              - magic constant 0xbe6d4a8b
              - written byte-by-byte by HAL_FLASH_Program(0x0800c000 + i)
              - a high-water / range constant 0x08080000
            flash HAL lock @0x0800433c

  v3.1.5.0  same HAL, but shifted (-0x2ec) and NO 0xbe6d4a8b anywhere.

That is a concrete, falsifiable difference in the persistence path - exactly the
kind of thing U5 ("what did 3.2.D.8 change?") needs.  This script:

  1. locates the HAL_FLASH_Unlock function in each image via the key literals
  2. finds its callers (the save routines)
  3. disassembles both save routines side by side
  4. reports literal-pool differences between the two routines

usage:
  python tools\\servo_persist_cmp.py <a.bin> <b.bin>
"""
import sys, struct

FLASH_BASE = 0x08000000
KEY1, KEY2 = 0x45670123, 0xCDEF89AB


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def sites_of_dword(flash, val):
    return [FLASH_BASE + o for o in range(0, len(flash) - 4, 4)
            if struct.unpack_from('<I', flash, o)[0] == val]


def ldr_pc_targets(flash, md):
    """Map: address of `ldr rX,[pc,#n]` -> target literal address."""
    out = {}
    for a in range(FLASH_BASE, FLASH_BASE + len(flash) - 4, 2):
        for i in md.disasm(flash[a - FLASH_BASE:a - FLASH_BASE + 4], a):
            if i.mnemonic == 'ldr' and 'pc' in i.op_str:
                try:
                    off = int(i.op_str.split('#')[-1].rstrip(']'), 0)
                except ValueError:
                    break
                out[i.address] = ((i.address + 4) & ~3) + off
            break
    return out


def callers_of(flash, md, target):
    out = []
    t = target & ~1
    for a in range(FLASH_BASE, FLASH_BASE + len(flash) - 4, 2):
        for i in md.disasm(flash[a - FLASH_BASE:a - FLASH_BASE + 4], a):
            if i.mnemonic in ('bl', 'blx') and i.op_str.startswith('#'):
                try:
                    if (int(i.op_str[1:], 0) & ~1) == t:
                        out.append(i.address)
                except ValueError:
                    pass
            break
    return out


def main(argv):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)

    res = {}
    for path in argv:
        flash, _b, _f = load(path)
        print("\n######## %s (%d B) ########" % (path, len(flash)))
        k1 = sites_of_dword(flash, KEY1)
        k2 = sites_of_dword(flash, KEY2)
        print("  FLASH_KEY1 literal sites: %s" % [hex(x) for x in k1])
        print("  FLASH_KEY2 literal sites: %s" % [hex(x) for x in k2])

        # unlock function = the routine that loads both keys; find its entry by
        # scanning back for the nearest `ldr r0,[pc,#..]` cluster (the function
        # head is the first instruction of the enclosing stub)
        unlock = None
        for ldr_site, tgt in sorted(ldr_pc_targets(flash, md).items()):
            if tgt == k1[0] if k1 else False:
                unlock = ldr_site
        print("  unlock function key-load site: %s" % (hex(unlock) if unlock else "?"))
        print("  magic 0xbe6d4a8b sites: %s" % [hex(x) for x in sites_of_dword(flash, 0xbe6d4a8b)])
        res[path] = flash

    print("\n######## side-by-side of the two save routines ########")
    # known from the v3.2.D.8 analysis
    A = (argv[0], 0x080017d0, 0x08001910)
    B = (argv[1], 0x080014e4, 0x08001624)   # guess: shifted by -0x2ec
    for path, lo, hi in (A, B):
        flash = res[path]
        print("\n---- %s  0x%08x..0x%08x ----" % (path, lo, hi))
        ln = hi - lo
        if lo - FLASH_BASE + ln > len(flash):
            print("  (out of range)")
            continue
        for i in md.disasm(flash[lo - FLASH_BASE:lo - FLASH_BASE + ln], lo):
            note = ""
            if i.mnemonic == 'ldr' and 'pc' in i.op_str:
                try:
                    off = int(i.op_str.split('#')[-1].rstrip(']'), 0)
                    tgt = ((i.address + 4) & ~3) + off
                    if FLASH_BASE <= tgt <= FLASH_BASE + len(flash) - 4:
                        note = "  ; = 0x%08x" % struct.unpack_from('<I', flash, tgt - FLASH_BASE)[0]
                except ValueError:
                    pass
            print("  %08x: %-8s %-26s%s" % (i.address, i.mnemonic, i.op_str, note))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
