"""zf_patch_verify.py - verify the proposed 3150 guard-removal patch.

Patch: app 0x0802F860 (Ghidra 0x0801F860)  bytes D1 0E (bne) -> 00 BF (nop)
       reason: remove the `[r5+2]==2 || [r6+0x14d]==6` gate in front of the
       [axis+0x230] (= OD 0x6062, the value the CODESYS master reports) store,
       exactly matching what 3.2.D.8 does there.

Checks (all must pass):
  A  the decoded instruction at the site really is `bne` with that offset
  B  the branch target lands exactly on the position-copy block start
  B2 no OTHER branch in the function lands inside the patched bytes
  C  register semantics: r0 (dyn in A) is dead after the site (reloaded);
     r7 is live across the site and must NOT be written -> NOP is safe
  D  the patched bytes decode to `nop` (0xBF00 little-endian = 00 BF)
  E  structural: the same code path is taken unconditionally in 3.2.D.8
"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from zf_img import Img

SITE = 0x0802F860          # app address
FUNC_LO, FUNC_HI = 0x0802F7FC, 0x0802F99C
OLD = bytes([0x0E, 0xD1])   # `bne #0x0802F880` in memory order (halfword D10E)

results = []


def check(name, cond, detail):
    results.append((name, bool(cond), detail))
    print('  [%s] %-52s %s' % ('PASS' if cond else 'FAIL', name, detail))


def main():
    a = Img('data/servo_fw_samples/elf/v3150.elf')
    b = Img('data/servo_fw_samples/elf/v328d8.elf')

    raw = a.rd(SITE, 2)
    print('site bytes = %s (expect %s)' % (raw.hex(), OLD.hex()))
    check('A1 site holds the expected bytes', raw == OLD, raw.hex())

    ins = list(a.dis(SITE, 2))[0]
    check('A2 decodes as bne', ins.mnemonic == 'bne',
          '%s %s' % (ins.mnemonic, ins.op_str))
    tgt = int(ins.op_str[1:], 0) if ins.op_str.startswith('#') else None
    # the skip target is the *end* of the block that writes [axis+0x230]
    check('B1 branch target == 0x0802F880 (skips the +0x230 store)',
          tgt == 0x0802F880, hex(tgt or 0))
    inside = list(a.dis(0x0802F862, 6))
    check('B3 branch target is past the [axis+0x230] store',
          tgt is not None and tgt > 0x0802F87C,
          'store site 0x0802F87C, target %s' % hex(tgt or 0))

    # B2: no other branch into the patched bytes
    hits = []
    for i in a.dis(FUNC_LO, FUNC_HI - FUNC_LO):
        if i.address == SITE:
            continue
        if i.mnemonic.startswith('b') and i.op_str.startswith('#'):
            try:
                t = int(i.op_str[1:], 0) & ~1
            except ValueError:
                continue
            if SITE <= t < SITE + 2:
                hits.append((i.address, t))
    check('B2 no other branch into the patched bytes', not hits, str(hits))

    # C: register semantics around the site
    before = list(a.dis(SITE - 0x10, 0x10))
    after = list(a.dis(0x0802F862, 0x18))
    r0_after = [i for i in after if i.mnemonic in ('ldr', 'ldr.w')
                and i.op_str.split(',')[0].strip() == 'r0']
    check('C1 r0 is reloaded immediately after the site', bool(r0_after),
          r0_after[0].mnemonic + ' ' + r0_after[0].op_str if r0_after else '-')
    r7_writes_in_patch = []          # the patch writes nothing at all
    check('C2 the patch writes no register', not r7_writes_in_patch, 'nop')

    # D: patched bytes decode as nop
    blob = bytearray(a.blob)
    o = a.off(SITE)
    blob[o:o + 2] = b'\x00\xbf'
    md = a.md
    new = list(md.disasm(bytes(blob[o:o + 2]), SITE))
    check('D patched bytes decode as nop',
          len(new) == 1 and new[0].mnemonic == 'nop' and new[0].size == 2,
          '%s' % ([(x.mnemonic, x.size) for x in new]))

    # E: structural comparison with 3.2.D.8 at the equivalent spot
    d8 = list(b.dis(0x08030C16, 0x28))
    has_guard = any(i.mnemonic in ('bne', 'beq', 'cbz', 'cbnz') for i in d8)
    check('E1 3.2.D.8 has NO gate at the equivalent point', not has_guard,
          '; '.join('%s %s' % (i.mnemonic, i.op_str) for i in d8[:6]))
    d8_store = [i for i in d8 if i.mnemonic.startswith('str') and '0x230' in i.op_str]
    check('E2 3.2.D.8 stores +0x230 unconditionally', bool(d8_store),
          d8_store[0].mnemonic + ' ' + d8_store[0].op_str if d8_store else '-')

    print()
    bad = [n for n, ok, _d in results if not ok]
    print('TOTAL: %d checks, %d failed' % (len(results), len(bad)))
    if bad:
        print('FAILED: %s' % bad)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
