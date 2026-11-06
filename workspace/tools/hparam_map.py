"""hparam_map.py - build the authoritative H-parameter <-> EtherCAT address map from
the OFFICIAL Dobot servo parameter CSVs.

Why this exists
---------------
SERVO_FW_OD_FINDING.md blocker A says: "the OD metadata table contains neither an
object index nor a vendor parameter address; the mapping from a table entry to a
real parameter address must be computed by code (or held in a separate array) -
finding that mapping is the next step."

The mapping is documented by the VENDOR.  data/official/servoCSV/param.csv is the
master parameter table:

    ParaIndex      H00.00, H00.01, ...        <- human name (H group . sub)
    ParaMapIndex   0, 1, ...                  <- the parameter map index
    ParaName       (GBK Chinese) parameter name

and the field-observed EtherCAT address encoding is

    addr + hex(0x2000 + H-group) + 2-digit-decimal(subindex + 1)
        H0C.00 -> 0x200C subIndex 1
        H01.17 -> 0x2001 subIndex 18

so ParaMapIndex is the vendor parameter-map index and (H-group, H-sub) maps to
(0x2000|group, sub+1).  This script extracts and cross-checks that table, and
verifies the relationship ParaMapIndex <-> (group, sub).

Files are GBK (not UTF-8) - decode accordingly.

usage:
  python tools\\hparam_map.py                      # default CSVs in data/official/servoCSV
  python tools\\hparam_map.py --csv <path>
  python tools\\hparam_map.py --find H0C
  python tools\\hparam_map.py --verify             # check ParaMapIndex <-> (group,sub)
  python tools\\hparam_map.py --json out.json
"""
import sys, os, csv, io, json, re

DEFAULT_DIR = os.path.join('data', 'official', 'servoCSV')
ENCODINGS = ('gbk', 'gb18030', 'utf-8-sig', 'utf-8')


def read_text(path):
    raw = open(path, 'rb').read()
    for enc in ENCODINGS:
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return raw.decode('latin-1'), 'latin-1'


def parse_param_csv(path):
    """param.csv: master table.  Returns list of dicts keyed by ParaIndex."""
    text, enc = read_text(path)
    rows = list(csv.reader(io.StringIO(text)))
    hdr_i = None
    for i, r in enumerate(rows):
        if r and r[0].strip() == 'IsCheck':
            hdr_i = i
            break
    if hdr_i is None:
        raise SystemExit("no header row in %s" % path)
    hdr = [h.strip() for h in rows[hdr_i]]
    out = []
    for r in rows[hdr_i + 1:]:
        if not r or not r[0].strip():
            continue
        d = dict(zip(hdr, r))
        pi = d.get('ParaIndex', '').strip()
        m = re.match(r'^H([0-9A-Fa-f]{2})\.(\d+)$', pi)
        if not m:
            continue
        grp = int(m.group(1), 16)
        sub = int(m.group(2), 10)
        try:
            mi = int(d.get('ParaMapIndex', '').strip() or -1)
        except ValueError:
            mi = -1
        out.append({
            'para_index': pi, 'group': grp, 'sub': sub, 'map_index': mi,
            'name': d.get('ParaName', '').strip(),
            'value': d.get('ParaValue', '').strip(),
            'min': d.get('MIN', '').strip(), 'max': d.get('MAX', '').strip(),
            'unit': d.get('Unit', '').strip(),
            'ro': d.get('ReadOnly', '').strip().upper() == 'TRUE',
            'immediate': d.get('EffectImmediate', '').strip().upper() == 'TRUE',
            'level': d.get('SaftyLevel', '').strip(),
            'category': d.get('GroupCatogary', '').strip(),
            'ethercat': '0x%04X:%d' % (0x2000 | grp, sub + 1),
        })
    return out, enc


def parse_axis_csv(path):
    text, enc = read_text(path)
    rows = list(csv.reader(io.StringIO(text)))
    hdr_i = None
    for i, r in enumerate(rows):
        if r and r[0].strip() == 'ParaIndStr':
            hdr_i = i
            break
    if hdr_i is None:
        return [], enc
    hdr = [h.strip() for h in rows[hdr_i]]
    out = []
    for r in rows[hdr_i + 1:]:
        if not r or not r[0].strip():
            continue
        d = dict(zip(hdr, r))
        out.append({'para_index': d.get('ParaIndStr', '').strip(),
                    'map_index': d.get('ParaMapIndStr', '').strip(),
                    'name': d.get('ParaName', '').strip(),
                    'value': d.get('ParaValue', '').strip()})
    return out, enc


def main(argv):
    csvdir = argv[argv.index('--csv') + 1] if '--csv' in argv else DEFAULT_DIR
    p = os.path.join(csvdir, 'param.csv') if os.path.isdir(csvdir) else csvdir
    if not os.path.exists(p):
        raise SystemExit("missing %s" % p)

    ents, enc = parse_param_csv(p)
    print("param.csv decoded as %s: %d H-parameters" % (enc, len(ents)))

    groups = {}
    for e in ents:
        groups.setdefault(e['group'], []).append(e)
    print("  groups: %s" % ', '.join('H%02X(%d)' % (g, len(v))
                                     for g, v in sorted(groups.items())))

    mi = [e['map_index'] for e in ents if e['map_index'] >= 0]
    print("  map_index range %d..%d, distinct %d, dupes %d" %
          (min(mi), max(mi), len(set(mi)), len(mi) - len(set(mi))))

    print("\n=== verify the field encoding rule against the vendor table ===")
    print("  rule: H<gg>.<ss>  ->  EtherCAT index 0x20<gg>, subIndex ss+1")
    for want in ('H0C.00', 'H01.17', 'H00.00', 'H00.01'):
        hit = [e for e in ents if e['para_index'] == want]
        if hit:
            e = hit[0]
            print("    %-8s map=%-5d ethercat=%-12s name=%s" %
                  (e['para_index'], e['map_index'], e['ethercat'], e['name']))
        else:
            print("    %-8s NOT PRESENT in param.csv" % want)

    print("\n=== is ParaMapIndex == (group<<8 | sub) or a dense counter? ===")
    dense = all(e['map_index'] == i for i, e in enumerate(ents) if e['map_index'] >= 0)
    print("  dense counter 0,1,2,... : %s" % dense)
    packed = sum(1 for e in ents if e['map_index'] == ((e['group'] << 8) | e['sub']))
    print("  equals (group<<8|sub)   : %d / %d" % (packed, len(ents)))
    sub_is_map = sum(1 for e in ents if e['map_index'] == e['sub'])
    print("  equals sub              : %d / %d" % (sub_is_map, len(ents)))

    if '--find' in argv:
        pat = argv[argv.index('--find') + 1].upper()
        print("\n=== entries matching %s ===" % pat)
        for e in ents:
            if pat in e['para_index'].upper() or pat in e['name'].upper():
                print("    %-8s map=%-5d ec=%-12s ro=%-5s %s" %
                      (e['para_index'], e['map_index'], e['ethercat'], e['ro'], e['name']))

    if '--json' in argv:
        out = argv[argv.index('--json') + 1]
        json.dump(ents, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print("\nwrote %s" % out)

    # show the first 25 so the shape is visible
    print("\n=== first 25 entries ===")
    for e in ents[:25]:
        print("  %-8s map=%-4d ec=%-11s %s" %
              (e['para_index'], e['map_index'], e['ethercat'], e['name']))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
