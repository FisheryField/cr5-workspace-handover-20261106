"""servo_nvmap.py - locate and compare the non-volatile PARAMETER PERSISTENCE subsystem
in both servo firmware images.

Discovered in 3.2.D.8 (this session), by following literals with tools/thumb_dis.py
and tools/servo_xref_multi.py:

  0x080045A8  nonvolatile parameter API
                - if byte flag [0x2000348C] != 0  -> persist immediately
                - else stage into a RAM buffer at 0x20009714, byte count at
                  [0x20003494], capacity 0x180, error 0x8003 if overflow
                - mirrors the staging buffer into 0x200096E4+  (struct at 0x200096E4)

  0x08001708  persist routine (the only caller of the above's persist path)
                - requires buffer length >= 0x20
                - validates a 32-bit header magic 0xA1B2C3D4 at buffer[0]
                - skips the 0x20-byte header, word-copies the rest to flash
                  at the advancing pointer [0x20003470], +4 per word
                - error 0x800D on bad magic/length

  0x080017D0  log append
                - builds a 0x18-byte record, reads 16 bytes from 0x200096E8
                - magic 0xBE6D4A8B at record+0x14
                - byte-writes 0x18 bytes to 0x0800C000
                - high-water 0x08080000

  0x08009BF8  flash region classifier (returns 0,8,..,0x58 for 0x08004000..0x08100000)
  0x0800C000  base of the non-volatile parameter area in flash

This script reports, for each image, whether each of those landmarks exists and
where - which is the direct way to answer "did 3.2.D.8 change parameter
persistence?" without a byte diff.

usage:
  python tools\\servo_nvmap.py <a.bin> <b.bin>
"""
import sys, struct

FLASH_BASE = 0x08000000

LANDMARKS = [
    ('header magic A1B2C3D4', 0xA1B2C3D4),
    ('record magic BE6D4A8B', 0xBE6D4A8B),
    ('flash param base 0800C000', 0x0800C000),
    ('high-water 08080000', 0x08080000),
    ('RAM staging 20009714', 0x20009714),
    ('RAM mirror 200096E4', 0x200096E4),
    ('RAM flag 2000348C', 0x2000348C),
    ('RAM count 20003494', 0x20003494),
    ('RAM wptr 20003470', 0x20003470),
    ('FLASH_KEY1', 0x45670123),
    ('FLASH_KEY2', 0xCDEF89AB),
]


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def sites(flash, val):
    out = []
    for o in range(0, len(flash) - 4, 4):
        if struct.unpack_from('<I', flash, o)[0] == val:
            out.append(FLASH_BASE + o)
    return out


def main(argv):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)

    imgs = []
    for path in argv:
        flash, _b, _f = load(path)
        imgs.append((path, flash))

    print("=== landmark literal sites per image ===")
    hdr = "%-26s" % "landmark"
    for path, _f in imgs:
        hdr += "%-22s" % path.split('\\')[-1]
    print(hdr)
    table = {}
    for name, val in LANDMARKS:
        row = "%-26s" % name
        for path, flash in imgs:
            s = sites(flash, val)
            table[(path, val)] = s
            row += "%-22s" % (' '.join('0x%x' % x for x in s[:3]) if s else '-- ABSENT --')
        print(row)

    # function-presence probe: does an image contain the persist prologue pattern?
    print("\n=== persist-routine prologue probe (0x18 / 0xA1B2C3D4 / len>=0x20 checks) ===")
    for path, flash in imgs:
        magics = table[(path, 0xA1B2C3D4)]
        print("  %s : %d site(s)" % (path, len(magics)))
        for m in magics:
            # find the ldr that loads this literal and scan back for the function head
            for a in range(m - 0x20, max(FLASH_BASE, m - 0x200), -2):
                for i in md.disasm(flash[a - FLASH_BASE:a - FLASH_BASE + 4], a):
                    if i.mnemonic.startswith('push'):
                        print("       magic@0x%08x  function head ~0x%08x (%s %s)" %
                              (m, a, i.mnemonic, i.op_str))
                    break
                else:
                    continue
                break

    # compare the persist routine listing between the two images if both have it
    if len(imgs) == 2 and all(table[(p, 0xA1B2C3D4)] for p, _f in imgs):
        print("\n=== persist routine: instruction stream comparison ===")
        seqs = []
        for path, flash in imgs:
            m = table[(path, 0xA1B2C3D4)][0]
            head = None
            for a in range(m, max(FLASH_BASE, m - 0x300), -2):
                b = flash[a - FLASH_BASE:a - FLASH_BASE + 2]
                if len(b) == 2 and b[1] == 0xB5:
                    head = a
                    break
            listing = []
            if head:
                for i in md.disasm(flash[head - FLASH_BASE:head - FLASH_BASE + 0x120], head):
                    listing.append((i.mnemonic, i.op_str.split('#')[0].strip() if '#' in i.op_str else i.op_str))
            seqs.append((path, head, listing))
            print("  %s : head 0x%08x, %d insns" % (path, head or 0, len(listing)))
        if all(s[2] for s in seqs):
            a, b = seqs[0][2], seqs[1][2]
            n = min(len(a), len(b))
            same = sum(1 for i in range(n) if a[i] == b[i])
            print("  identical at same index: %d / %d (%.1f%%)" % (same, n, 100.0 * same / max(1, n)))
            shown = 0
            for i in range(n):
                if a[i] != b[i]:
                    print("    [%3d] A %-8s %-20s | B %-8s %s" % (i, a[i][0], a[i][1], b[i][0], b[i][1]))
                    shown += 1
                    if shown >= 15:
                        break
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
