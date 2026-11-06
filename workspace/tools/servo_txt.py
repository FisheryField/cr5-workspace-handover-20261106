"""servo_txt.py - compare only *plausible text* strings between two firmware
builds (filters out the garbage runs produced by disaligned code bytes).

A candidate must look like real text: mostly letters, contains a vowel, has a
space or a word of >=4 letters, and no long runs of punctuation.

usage:
  python tools\\servo_txt.py <new.bin> <old.bin>
  python tools\\servo_txt.py <new.bin> <old.bin> --kw start,h
"""
import sys, os, struct, re, collections

FLASH_BASE = 0x08000000
WORD = re.compile(r'[A-Za-z]{4,}')


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def is_text(s):
    """strict: real firmware text, not a run of code bytes that happen to be
    printable letters"""
    if len(s) < 6 or len(s) > 120:
        return False
    letters = sum(1 for c in s if c.isalpha())
    if letters < 0.75 * len(s):
        return False
    # real text has words of >=4 letters with vowels
    words = re.findall(r'[A-Za-z]{4,}', s)
    if len(words) < 2 and not re.search(r'[A-Za-z]{6,}', s):
        return False
    if sum(1 for w in words if re.search(r'[aeiouAEIOU]', w)) < 1:
        return False
    # uppercase soup with no vowels anywhere is code noise
    if not re.search(r'[aeiou]', s):
        return False
    if re.search(r'[^A-Za-z0-9 _\-./:;,%()\[\]{}+=*<>#\'"!?@&|~^$\\]', s):
        return False
    # a repeated 4-gram is the signature of instruction noise
    for i in range(len(s) - 4):
        if s.count(s[i:i + 4]) >= 3:
            return False
    # words should not be all-consonant gibberish runs longer than 8
    if re.search(r'[^aeiouAEIOU0-9 _\-./:;,%()\[\]]{9,}', s):
        return False
    return True


def texts(flash):
    c = collections.Counter()
    for mt in re.finditer(rb'[\x20-\x7e]{6,}', flash):
        s = mt.group().decode('ascii')
        if is_text(s):
            c[s.strip()] += 1
    return c


def main(argv):
    new_p, old_p = argv[0], argv[1]
    _dn, _bn, fn = load(new_p)
    _do, _bo, fo = load(old_p)
    sn, so = texts(fn), texts(fo)
    print("new %s: %d text strings" % (os.path.basename(new_p), len(sn)))
    print("old %s: %d text strings" % (os.path.basename(old_p), len(so)))
    common = set(sn) & set(so)
    only_new = sorted(set(sn) - set(so))
    only_old = sorted(set(so) - set(sn))
    print("common %d / only in new %d / only in old %d" % (len(common), len(only_new), len(only_old)))
    print()
    if '--kw' in argv:
        for kw in argv[argv.index('--kw') + 1].split(','):
            kw = kw.strip().lower()
            print("=== %r ===" % kw)
            for s in sorted(sn):
                if kw in s.lower():
                    print("   NEW %r" % s)
            for s in sorted(so):
                if kw in s.lower():
                    print("   OLD %r" % s)
            print()
        return 0
    print("=== only in NEW (%d) ===" % len(only_new))
    for s in only_new:
        print("   + %r" % s)
    print()
    print("=== only in OLD (%d) ===" % len(only_old))
    for s in only_old:
        print("   - %r" % s)
    print()
    print("=== common but worth reading (%d) ===" % len(common))
    for s in sorted(common)[:80]:
        print("   = %r" % s)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
