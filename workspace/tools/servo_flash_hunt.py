"""servo_flash_hunt.py - locate non-volatile (flash) storage code in a servo image.

Rationale: the only thing that differs between servo DS.3.1.5.0 (zero point not
retained) and DS.3.2.D.8 (zero point retained) is that the newer drive SURVIVES
a power cycle.  Whatever the mechanism, it must write to non-volatile memory.
This image is a Cortex-M flash image mapped at 0x08000000, so the part is an
STM32-family MCU and its flash controller lives in the peripheral block.

This script searches for the tell-tale constants instead of guessing at tables:

  * STM32 flash interface registers
      0x40022000  FLASH base (F1/F2)     0x40023C00  FLASH base (F4/F7)
      0x40022004  FLASH_KEYR             0x4002200C  FLASH_CR
      0x40022010  FLASH_SR               0x40022014  FLASH_AR
  * the standard unlock keys
      0x45670123 / 0xCDEF89AB
  * option-byte / write-protection register bases (F1: 0x1FFFF800)

Both `movw/movt` immediate pairs and PC-relative literal pools are searched, so
that a hit is reported wherever the constant really lives.

usage:
  python tools\\servo_flash_hunt.py <flash.bin>
  python tools\\servo_flash_hunt.py <flash.bin> --diff <other.bin>
"""
import sys, struct, re

FLASH_BASE = 0x08000000

REGISTERS = {
    0x40022000: "FLASH base (STM32F1/F2)",
    0x40022004: "FLASH_KEYR",
    0x40022008: "FLASH_OPTKEYR",
    0x4002200C: "FLASH_CR (F1)",
    0x40022010: "FLASH_SR (F1)",
    0x40022014: "FLASH_AR (F1)",
    0x40023C00: "FLASH base (STM32F4/F7)",
    0x40023C04: "FLASH_KEYR (F4)",
    0x40023C0C: "FLASH_CR (F4)",
    0x40023C10: "FLASH_SR (F4)",
    0x40023C14: "FLASH_CR2 (F4)",
    0x1FFFF800: "option bytes (F1)",
    0x1FFFC000: "option bytes (F4)",
}
KEYS = {0x45670123: "FLASH_KEY1", 0xCDEF89AB: "FLASH_KEY2"}


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def scan_dwords(flash, wanted):
    """All 4-byte-aligned dwords equal to a wanted value."""
    out = {v: [] for v in wanted}
    for o in range(0, len(flash) - 4, 4):
        v = struct.unpack_from('<I', flash, o)[0]
        if v in out:
            out[v].append(FLASH_BASE + o)
    return out


def thumb_movwt(flash, wanted):
    """Idiomatic `movw rX,#lo16 ; movt rX,#hi16` pairs anywhere (byte aligned)."""
    out = {v: [] for v in wanted}
    for o in range(0, len(flash) - 8, 2):
        a, b = struct.unpack_from('<HH', flash, o)
        # movw:  11110 i 10 0100 imm4 | 0 imm3 rd imm8
        # movt:  11110 i 10 1100 imm4 | 0 imm3 rd imm8
        if (a & 0xFB00) != 0xF200 or (b & 0x8000):
            continue
        if (a & 0x0080) != 0:      # imm4 high bit must be 0 for our constants
            continue
        op = (a >> 4) & 0xF
        if op not in (4, 12):
            continue
        imm4 = (a >> 4 & 0)  # placeholder
        i = (a >> 10) & 1
        imm4b = a & 0xF
        imm3 = (b >> 12) & 0x7
        imm8 = b & 0xFF
        v = (i << 11) | (imm4b << 12) | (imm3 << 8) | imm8
        if v in out:
            out[v].append(FLASH_BASE + o)
    return out


def main(argv):
    path = argv[0]
    _d, _hdr, flash = load(path)
    print("image 0x%08x..0x%08x (%d B)" % (FLASH_BASE, FLASH_BASE + len(flash), len(flash)))

    wanted = list(REGISTERS) + list(KEYS)
    names = dict(REGISTERS)
    names.update(KEYS)

    dw = scan_dwords(flash, wanted)
    print("\n=== literal-pool dwords (4-byte aligned) ===")
    total = 0
    for v in wanted:
        if dw[v]:
            total += len(dw[v])
            print("  0x%08x %-28s %d sites: %s" %
                  (v, names[v], len(dw[v]),
                   ' '.join('0x%08x' % a for a in dw[v][:10])))
    print("  total literal sites: %d" % total)

    print("\n=== movw/movt immediate pairs ===")
    total2 = 0
    for v in wanted:
        if thumb_movwt(flash, [v])[v]:
            sites = thumb_movwt(flash, [v])[v]
            total2 += len(sites)
            print("  0x%08x %-28s %d sites: %s" %
                  (v, names[v], len(sites),
                   ' '.join('0x%08x' % a for a in sites[:10])))
    print("  total movw/movt sites: %d" % total2)

    if '--diff' in argv:
        other = argv[argv.index('--diff') + 1]
        _d2, _h2, flash2 = load(other)
        print("\n=== diff vs %s ===" % other)
        n = min(len(flash), len(flash2))
        same = sum(1 for i in range(n) if flash[i] == flash2[i])
        print("  common %d B, identical bytes %d (%.2f%%)" % (n, same, 100.0 * same / n))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
