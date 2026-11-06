"""fix_od_finding.py - repair the control-byte corruption in SERVO_FW_OD_FINDING.md.

Diagnosis (2026-09-23): the file contains 13 stray control bytes - 10 NUL (0x00)
and 3 BEL (0x07) - produced by a string-escaping bug when the document was
written.  Every one of them replaces the first character of a literal token:

    TAB  (0x09) for 't'   ->  <TAB>ools/od_refs2.py        should be  tools/od_refs2.py
    BEL  (0x07) for 'a'   ->  <BEL>ddr200C01               should be  addr200C01
    NUL  (0x00) for '0'   ->  <NUL>x080513cc               should be  0x080513cc

Because the substituted characters are exactly the ones a naive formatter would
treat as escapes (\\t, \\a, \\0), the original text is unambiguous.  This script
performs the substitution with an explicit expected-count assertion per rule so a
future re-run cannot silently mangle the file, and backs up the original first.

usage:
  python tools\\fix_od_finding.py --check      # report only, write nothing
  python tools\\fix_od_finding.py --apply
"""
import sys, os, shutil, datetime

DOC = os.path.join('SERVO_FW_OD_FINDING.md')

TAB, BEL, NUL = '\x09', '\x07', '\x00'

# (literal-to-find, replacement, expected number of occurrences)
RULES = [
    (TAB + 'ools/',            'tools/',            1),
    (BEL + 'ddr',              'addr',             3),
    (NUL + 'x',                '0x',              10),
]


def main(argv):
    if not os.path.exists(DOC):
        raise SystemExit("missing %s" % DOC)
    raw = open(DOC, 'rb').read()
    text = raw.decode('utf-8')
    before = {repr(TAB): text.count(TAB), repr(BEL): text.count(BEL), repr(NUL): text.count(NUL)}
    print("control bytes present: TAB=%d BEL=%d NUL=%d" % (text.count(TAB), text.count(BEL), text.count(NUL)))

    total_expected = sum(n for _a, _b, n in RULES)
    total_found = sum(text.count(a) for a, _b, _n in RULES)
    print("rule-matched occurrences: %d (rules expect %d)" % (total_found, total_expected))

    ok = True
    for a, b, n in RULES:
        c = text.count(a)
        status = "OK" if c == n else "MISMATCH"
        if c != n:
            ok = False
        print("  %-28r -> %-12r found=%d expected=%d  %s" %
              (a, b, c, n, status))

    # every control byte must be accounted for by a rule
    left = text.count(TAB) + text.count(BEL) + text.count(NUL) - total_found
    print("unaccounted control bytes: %d" % left)
    if left != 0 or not ok:
        if '--apply' in argv:
            raise SystemExit("REFUSING to apply: rules do not account for the file exactly")
        print("(dry run - nothing written)")
        return 1

    if '--check' in argv or '--apply' not in argv:
        print("\nall rules verified; nothing written (pass --apply to fix)")
        return 0

    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    bak = DOC + '.bak_' + stamp
    shutil.copy2(DOC, bak)
    for a, b, _n in RULES:
        text = text.replace(a, b)
    open(DOC, 'w', encoding='utf-8', newline='').write(text)

    after = open(DOC, 'rb').read()
    print("\nbackup  -> %s" % bak)
    print("written -> %s (%d bytes, was %d)" % (DOC, len(after), len(raw)))
    at = after.decode('utf-8')
    print("control bytes remaining: TAB=%d BEL=%d NUL=%d CR=%d" %
          (at.count(TAB), at.count(BEL), at.count(NUL), at.count('\r')))
    print("\nrepaired lines:")
    for i, ln in enumerate(at.split('\n')):
        if any(s in ln for s in ('tools/od_refs2.py', '0x080513cc', '0x09801401',
                                 'addr + hex', 'addr200C01', '0x200C:1', '0x20 当')):
            print("  L%-4d %s" % (i + 1, ln.rstrip()))
    return 0


if __name__ == "__main__":
    sys.exit(main(__import__('sys').argv[1:]))
