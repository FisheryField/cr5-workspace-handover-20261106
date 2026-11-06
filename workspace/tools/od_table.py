"""od_table.py - parse the CANopen object-dictionary *metadata* table of a Dobot
servo firmware image.

Record layout - recovered from the raw bytes of v3.2.D.8 and validated
entry-by-entry against the CiA402 standard object indices:

    +0x00  "Object name\\0"      ASCII, NUL terminated
    ...    6-byte record, each field little-endian with a zero high byte:
              +0  u16 type   0x02=i8 0x03=i16 0x04=i32 0x05=u8 0x06=u16 0x07=u32
              +2  u16 bits   8 / 16 / 32
              +4  u16 attr   access bitfield; 0x0007 = read/write, 0x0087 = read-only,
                             0x003f / 0x007f observed as well

Validated samples (name -> standard index -> entry type/bits):

    Abort connection option code 0x6007 u16/16 ; Control Word 0x6040 u16/16
    Status Word 0x6041 i16/16 ; Modes of Operation 0x6060 i8/8
    Position demand value 0x6062 i32/32 ; Position Actual Value 0x6064 u32/32
    Following error window 0x6065 u16/16 ; Target Position 0x607A i32/32
    Home offset 0x607C ; Homing method 0x6098 ; Gear ratio 0x6091

IMPORTANT - what this table does NOT contain: neither an object index nor a
manufacturer parameter address.  The mapping from a table entry to a real
parameter address must be computed by code (or held in a separate array).
Finding that mapping is the next step.

usage:
  python tools\\od_table.py <flash.bin> [--json out.json] [--raw]
  python tools\\od_table.py <flash.bin> --filter home,calib
  python tools\\od_table.py <flash.bin> --dump 0x08025060 0x180
"""
import sys, os, struct, json, re

FLASH_BASE = 0x08000000
TYPE = {0x02: 'i8', 0x03: 'i16', 0x04: 'i32', 0x05: 'u8', 0x06: 'u16', 0x07: 'u32'}
KNOWN = {
    'Abort connection option code': 0x6007, 'Error Code': 0x603F,
    'Control Word': 0x6040, 'Status Word': 0x6041,
    'Modes of Operation': 0x6060, 'Modes of Operation Display': 0x6061,
    'Position demand value': 0x6062, 'Position actual internal value': 0x6063,
    'Position Actual Value': 0x6064, 'Following error window': 0x6065,
    'Following error time out': 0x6066, 'Position window': 0x6067,
    'Velocity sensor actual value': 0x6069, 'Sensor selection code': 0x606A,
    'Velocity demand value': 0x606B, 'Velocity Actual Value': 0x606C,
    'Velocity window': 0x606D, 'Velocity window time': 0x606E,
    'Velocity threshold': 0x606F, 'Target torque': 0x6071,
    'Max torque': 0x6072, 'Max current': 0x6073, 'Torque demand value': 0x6074,
    'Motor rated current': 0x6075, 'Torque Actual Value': 0x6077,
    'Current actual value': 0x6078, 'DC link circuit voltage': 0x6079,
    'Target Position': 0x607A, 'Home offset': 0x607C, 'Polarity': 0x607E,
    'Max profile velocity': 0x607F, 'Max motor speed': 0x6080,
    'Profile velocity': 0x6081, 'Profile acceleration': 0x6083,
    'Profile deceleration': 0x6084, 'Motion profile type': 0x6086,
    'Gear ratio': 0x6091, 'Feed constant': 0x6092, 'Homing method': 0x6098,
    'Speed during search for zero': 0x6099,
}


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def parse(flash):
    out = []
    for m in re.finditer(rb'[\x20-\x7e]{4,}\x00', flash):
        name = m.group()[:-1].decode('ascii', 'replace')
        if not re.search(r'[aeiouAEIOU]', name) or not re.search(r'[A-Za-z]{4,}', name):
            continue
        j = m.end()
        if j + 6 > len(flash):
            continue
        t_lo, t_hi = flash[j], flash[j + 1]
        b_lo, b_hi = flash[j + 2], flash[j + 3]
        a_lo, a_hi = flash[j + 4], flash[j + 5]
        if t_hi or b_hi or a_hi:            # high byte must be zero
            continue
        if t_lo not in TYPE or b_lo not in (8, 16, 32) or a_lo < 3:
            continue
        out.append({"name": name, "entry": FLASH_BASE + m.start(),
                    "type": TYPE[t_lo], "bits": b_lo, "attr": a_lo,
                    "access": "ro" if a_lo & 0x80 else "rw",
                    "std_index": KNOWN.get(name),
                    "rec": flash[j:j + 6].hex(' ')})
    return out


def dump(flash, lo, ln):
    o = lo - FLASH_BASE
    for i in range(0, ln, 16):
        b = flash[o + i:o + i + 16]
        if not b:
            break
        asc = ''.join(chr(c) if 32 <= c < 127 else '.' for c in b)
        print("  0x%08x  %-47s |%s|" % (lo + i, b.hex(' '), asc))


def main(argv):
    path = argv[0]
    _d, _hdr, flash = load(path)
    if '--dump' in argv:
        lo = int(argv[argv.index('--dump') + 1], 16)
        ln = int(argv[argv.index('--dump') + 2], 16)
        print("=== raw 0x%08x..0x%08x ===" % (lo, lo + ln))
        dump(flash, lo, ln)
        return 0

    ents = parse(flash)
    print("%s: %d object-dictionary metadata entries" % (os.path.basename(path), len(ents)))
    if not ents:
        return 1
    lo = min(e['entry'] for e in ents)
    hi = max(e['entry'] for e in ents)
    print("  entry span 0x%08x..0x%08x (%d B)" % (lo, hi, hi - lo))
    print("  cross-checked against CiA402 standard index: %d entries" %
          sum(1 for e in ents if e['std_index']))

    filt = argv[argv.index('--filter') + 1].lower().split(',') if '--filter' in argv else None
    raw = '--raw' in argv
    for e in ents:
        if filt and not any(f.strip() in e['name'].lower() for f in filt):
            continue
        line = "  %-38s %-4s %2dbit attr=0x%04x %-3s %-8s @0x%08x" % (
            e['name'][:38], e['type'], e['bits'], e['attr'], e['access'],
            ("0x%04X" % e['std_index']) if e['std_index'] else "?", e['entry'])
        if raw:
            line += "  rec=[%s]" % e['rec']
        print(line)
    if '--json' in argv:
        out = argv[argv.index('--json') + 1]
        json.dump(ents, open(out, 'w'), indent=1)
        print("wrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
