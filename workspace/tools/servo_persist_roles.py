"""servo_persist_roles.py - compare the persist/API routines of the two servo images by
ROLE instead of by absolute RAM address.

Findings this rests on (this session):
  * both images contain the same persist routine, anchored by the header magic
    0xA1B2C3D4; heads determined by scanning back to the enclosing `push`:
        v3.2.D.8   0x080016de      v3.1.5.0   0x0800171e
  * disassembling them shows IDENTICAL code shape, e.g. both do
        cmp  r4, #0x20 ; ldr r1,[pc]=magic ; ldr r0,[r5] ; cmp r0,r1
        movs r2,#0x20  ; ldr r0,[pc]=staging_dst ; bl memcpy
        movs r0,#1     ; strb r0,[flag]
        ldr r0,[pc]=wptr ; ldr r1,[r7] ; ldr r0,[r0] ; bl HAL_FLASH_Program_word
        adds r0,r0,#4  ; str r0,[wptr]
  * but the RAM globals DIFFER between builds:
        v3.2.D.8   staging_dst 0x200096E4   flag 0x2000348C   wptr 0x20003470
        v3.1.5.0   staging_dst 0x200091FC   flag 0x20003384   wptr 0x20003380

So an earlier "5 landmarks ABSENT in 3.1.5.0" result was an artifact of comparing raw
RAM addresses across builds - it must be retracted.

This script prints both routines side by side with each literal annotated by role, so
the comparison is address-independent.

usage:
  python tools\\servo_persist_roles.py
"""
import sys, struct

FLASH_BASE = 0x08000000
IMAGES = [
    ('v3.2.D.8', r'data\servo_fw_samples\elf\v328d8.bin', 0x080016de),
    ('v3.1.5.0', r'data\servo_fw_samples\elf\v3150.bin', 0x0800171e),
]
WINDOW = 0x120


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def role_of(v, order):
    """Classify a literal value and assign a stable role tag."""
    if v == 0xA1B2C3D4:
        return 'HDR_MAGIC'
    if 0x20000000 <= v < 0x20050000:
        order.append(v)
        return 'RAM#%d' % len(order)
    if 0x08000000 <= v < 0x08100000:
        return 'FLASH_CONST'
    return 'CONST'


def main(argv):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)

    results = []
    for name, path, head in IMAGES:
        flash, _b, _f = load(path)
        order = []
        listing = []
        for i in md.disasm(flash[head - FLASH_BASE:head - FLASH_BASE + WINDOW], head):
            lit = None
            if i.mnemonic == 'ldr' and 'pc' in i.op_str:
                try:
                    off = int(i.op_str.split('#')[-1].rstrip(']'), 0)
                    tgt = ((i.address + 4) & ~3) + off
                    if FLASH_BASE <= tgt <= FLASH_BASE + len(flash) - 4:
                        lit = struct.unpack_from('<I', flash, tgt - FLASH_BASE)[0]
                except ValueError:
                    pass
            listing.append((i.address, i.mnemonic, i.op_str, lit))
        # annotate
        ann = []
        for a, mn, ops, lit in listing:
            tag = ''
            if lit is not None:
                tag = '  ; %s = 0x%08x' % (role_of(lit, order), lit)
            ann.append((a, mn, ops, tag))
        results.append((name, head, ann, order))

    for name, head, ann, order in results:
        print("\n######## %s  persist routine @0x%08x ########" % (name, head))
        for a, mn, ops, tag in ann:
            print("  %08x: %-9s %-24s%s" % (a, mn, ops, tag))
        print("  RAM globals in program order: %s" % ' '.join('0x%08x' % v for v in order))

    print("\n######## role-by-role comparison ########")
    if len(results) == 2:
        n = min(len(results[0][2]), len(results[1][2]))
        same = 0
        diffs = []
        for i in range(n):
            a1, m1, o1, _t1 = results[0][2][i]
            a2, m2, o2, _t2 = results[1][2][i]
            # compare shape: mnemonic + operand text with immediates kept
            if m1 == m2 and o1 == o2:
                same += 1
            else:
                diffs.append((i, m1, o1, m2, o2))
        print("  identical (mnemonic + full operands): %d / %d (%.1f%%)" %
              (same, n, 100.0 * same / max(1, n)))
        for i, m1, o1, m2, o2 in diffs[:20]:
            print("    [%3d] A %-9s %-22s | B %-9s %s" % (i, m1, o1, m2, o2))
        print("\n  RAM global counts: A=%d B=%d" %
              (len(results[0][3]), len(results[1][3])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
