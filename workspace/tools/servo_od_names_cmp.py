"""servo_od_names_cmp.py - print the OD metadata name tables of both servo images side by
side and diff them, then match them against the official vendor H-parameter list.

Motivation: earlier documentation claims "the two firmware versions' object-dictionary
name tables are each 159 entries and completely identical".  That claim underpins the
conclusion that the fix is NOT a new vendor object - but the comparison was never
displayed.  This script makes it falsifiable:

  * extract the OD metadata records (name + type/bits/attr) from each image
  * diff the name lists
  * match names against data/servo_fw_samples/hparam_map.json (the official 259 H-params)
    to see whether vendor parameters are represented in the OD at all

usage:
  python tools\\servo_od_names_cmp.py <a.bin> <b.bin>
  python tools\\servo_od_names_cmp.py <a.bin> <b.bin> --json out.json
"""
import sys, os, json, re, struct

FLASH_BASE = 0x08000000
DEFAULT_HPARAM = os.path.join('data', 'servo_fw_samples', 'hparam_map.json')


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def od_records(flash):
    """OD metadata records: printable name\\0 followed by a valid type/bits descriptor."""
    TYPE = {0x02: 'i8', 0x03: 'i16', 0x04: 'i32', 0x05: 'u8', 0x06: 'u16', 0x07: 'u32'}
    out = []
    for m in re.finditer(rb'[\x20-\x7e]{4,}\x00', flash):
        name = m.group()[:-1].decode('ascii', 'replace')
        if not re.search(r'[aeiouAEIOU]', name) or not re.search(r'[A-Za-z]{4,}', name):
            continue
        j = m.end()
        if j + 6 > len(flash):
            continue
        t, th, b, bh, a, ah = flash[j:j + 6]
        if th == 0 and bh == 0 and ah == 0 and t in TYPE and b in (8, 16, 32):
            out.append({'name': name, 'entry': FLASH_BASE + m.start(),
                        'type': TYPE[t], 'bits': b, 'attr': a})
    return out


def main(argv):
    imgs = [p for p in argv if p.endswith('.bin')]
    if len(imgs) != 2:
        raise SystemExit("need two .bin paths")
    recs = {}
    for p in imgs:
        flash = load(p)[2]
        recs[p] = od_records(flash)

    for p in imgs:
        r = recs[p]
        print("### %s : %d OD metadata records" % (p, len(r)))

    A, B = recs[imgs[0]], recs[imgs[1]]
    na = [x['name'] for x in A]
    nb = [x['name'] for x in B]
    sa, sb = set(na), set(nb)
    print("\n=== name-set diff ===")
    print("  distinct names  A=%d  B=%d  shared=%d" % (len(sa), len(sb), len(sa & sb)))
    only_a = sorted(sa - sb)
    only_b = sorted(sb - sa)
    print("  only in A (%d): %s" % (len(only_a), only_a[:40]))
    print("  only in B (%d): %s" % (len(only_b), only_b[:40]))

    # type/bits/attr agreement on shared names
    da = {x['name']: (x['type'], x['bits'], x['attr']) for x in A}
    db = {x['name']: (x['type'], x['bits'], x['attr']) for x in B}
    diffs = [(n, da[n], db[n]) for n in sorted(sa & sb) if da[n] != db[n]]
    print("\n=== shared names whose type/bits/attr DIFFER ===")
    if diffs:
        for n, x, y in diffs:
            print("    %-40s A=%s  B=%s" % (n, x, y))
    else:
        print("    (none) - all shared names have identical metadata")

    # ordering identical?
    print("\n=== ordering ===")
    print("  same order: %s" % (na == nb))
    if na != nb and len(na) == len(nb):
        first = next((i for i in range(len(na)) if na[i] != nb[i]), None)
        print("  first divergence at index %s: A=%r B=%r" %
              (first, na[first] if first is not None else None,
               nb[first] if first is not None else None))

    # vendor H-parameter match
    if os.path.exists(DEFAULT_HPARAM):
        hp = json.load(open(DEFAULT_HPARAM, encoding='utf-8'))
        print("\n=== do OD names correspond to official H-parameter names? ===")
        print("  official H-params: %d (Chinese names, e.g. %s)" %
              (len(hp), ' / '.join(x['name'] for x in hp[:3])))
        # OD names are ASCII English; official names are Chinese -> compare structurally
        print("  OD names are ASCII English; official names are Chinese => direct string")
        print("  matching is not meaningful.  Recorded here so the negative is explicit.")
        vendorish = [x['name'] for x in A if re.match(r'^(Facturer|Vendor|Dobot|CR)', x['name'])]
        print("  vendor-flavoured OD names in A: %s" % (vendorish or '(none)'))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
