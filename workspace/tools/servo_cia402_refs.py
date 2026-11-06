"""servo_cia402_refs.py - find code that materialises a CiA402 object index.

Rationale: the firmware must compare/assign object indices when it services the
object dictionary and the PDO mapping. A CiA402 index such as 0x6064 (Position
Actual Value) is a 16-bit constant, so it shows up either
  * as a movw/movs immediate, or
  * as a halfword in a literal pool, or
  * inside a PDO mapping entry (`index` u16 + `subindex` u8 + `bits` u8) in data.

This script reports all three, then focuses on the objects that matter for the
zero-point question:

  0x6064 Position Actual Value      0x6062 Position demand value
  0x6063 Position actual internal   0x6061 Modes of operation display
  0x6060 Modes of operation         0x6040 Control word
  0x6041 Status word                0x607A Target position
  0x607C Home offset                0x6098 Homing method

usage:
  python tools\\servo_cia402_refs.py <flash.bin>
  python tools\\servo_cia402_refs.py <flash.bin> --idx 0x6064
  python tools\\servo_cia402_refs.py <flash.bin> --pdo
"""
import sys, struct, re

FLASH_BASE = 0x08000000

KEY = {
    0x6007: 'Abort connection option code',
    0x603F: 'Error code',
    0x6040: 'Control word',
    0x6041: 'Status word',
    0x6060: 'Modes of operation',
    0x6061: 'Modes of operation display',
    0x6062: 'Position demand value',
    0x6063: 'Position actual internal value',
    0x6064: 'Position Actual Value',
    0x6065: 'Following error window',
    0x606C: 'Velocity actual value',
    0x6077: 'Torque actual value',
    0x607A: 'Target position',
    0x607C: 'Home offset',
    0x607D: 'Software position limit',
    0x607E: 'Polarity',
    0x607F: 'Max profile velocity',
    0x6081: 'Profile velocity',
    0x6091: 'Gear ratio',
    0x6092: 'Feed constant',
    0x6098: 'Homing method',
    0x6099: 'Homing speeds',
}


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def thumb_imms(flash):
    """Yield (addr, immediate) for Thumb movw/movs/mov immediate encodings.

    Only mov*m* forms carry a 16-bit literal; we decode the common ones:
      movs rX,#imm8      (0x20-0x27 opcode family)
      movw rX,#imm16
    and also pick up cmp/add/sub immediate forms for completeness.
    """
    out = []
    a = FLASH_BASE
    n = len(flash)
    while a <= FLASH_BASE + n - 4:
        hw = struct.unpack_from('<H', flash, a - FLASH_BASE)[0]
        hw2 = struct.unpack_from('<H', flash, a - FLASH_BASE + 2)[0]
        # movs rX,#imm8  : 001 00 rd imm8
        if (hw & 0xF800) == 0x2000:
            out.append((a, hw & 0xFF, 'movs'))
        # movw rX,#imm16 : 11110 i 10 0100 imm4 | 0 imm3 rd imm8
        elif (hw & 0xFB00) == 0xF200 and ((hw >> 4) & 0xF) == 4 and not (hw2 & 0x8000):
            i = (hw >> 10) & 1
            imm4 = hw & 0xF
            imm3 = (hw2 >> 12) & 0x7
            imm8 = hw2 & 0xFF
            v = (i << 11) | (imm4 << 12) | (imm3 << 8) | imm8
            out.append((a, v, 'movw'))
        a += 2
    return out


def main(argv):
    path = argv[0]
    flash, _b, _f = load(path)
    print("image %s (%d B)" % (path, len(flash)))

    if '--idx' in argv:
        want = [int(argv[argv.index('--idx') + 1], 16)]
    else:
        want = sorted(KEY)

    print("\n=== CiA402 indices carried as an instruction immediate ===")
    imms = thumb_imms(flash)
    hits = {}
    for a, v, kind in imms:
        if v in want:
            hits.setdefault(v, []).append((a, kind))
    if not hits:
        print("  (none)")
    for v in sorted(hits):
        print("  0x%04X %-32s %d site(s): %s" %
              (v, KEY.get(v, ''), len(hits[v]),
               ' '.join('0x%x(%s)' % (a, k) for a, k in hits[v][:8])))

    print("\n=== CiA402 indices present as literal-pool halfwords (4-byte grid) ===")
    lits = {}
    for o in range(0, len(flash) - 4, 4):
        lo = struct.unpack_from('<H', flash, o)[0]
        if lo in want:
            lits.setdefault(lo, []).append(FLASH_BASE + o)
    if not lits:
        print("  (none)")
    for v in sorted(lits):
        print("  0x%04X %-32s %d site(s): %s" %
              (v, KEY.get(v, ''), len(lits[v]),
               ' '.join('0x%x' % a for a in lits[v][:8])))

    print("\n=== PDO-mapping style entries (index u16 | sub u8 | bits u8) for our indices ===")
    # a PDO mapping entry is index(u16) sub(u8) bits(u8); scan every 2-byte offset
    cnt = 0
    for o in range(0, len(flash) - 4, 2):
        idx, sub, bits = struct.unpack_from('<HBB', flash, o)
        if idx in want and bits in (1, 2, 4, 8, 16, 32) and sub < 0x40:
            print("    0x%08x : idx=0x%04X (%s) sub=%d bits=%d" %
                  (FLASH_BASE + o, idx, KEY.get(idx, ''), sub, bits))
            cnt += 1
            if cnt > 60:
                print("    ... (truncated)")
                break
    if cnt == 0:
        print("  (none)")
    else:
        print("  %d entr(ies)" % cnt)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
