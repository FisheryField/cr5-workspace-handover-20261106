"""servo_probe.py - identify the format of the servo firmware samples.

usage: python tools\\servo_probe.py <file> [<file> ...]
"""
import sys, struct, os, collections

for p in sys.argv[1:]:
    d = open(p, 'rb').read()
    print("=" * 90)
    print("%s  (%d bytes)" % (os.path.basename(p), len(d)))
    print("  md5 %s" % __import__('hashlib').md5(d).hexdigest())
    print("  head: %s" % d[:64].hex(' ', 4))
    sp, rv = struct.unpack_from('<II', d, 0)
    print("  as Cortex-M vector table: SP=0x%08x Reset=0x%08x  (valid=%s)" %
          (sp, rv, 0x20000000 <= sp <= 0x20040000 and 0x08000000 <= (rv & ~1) < 0x08200000))
    # is the file a libpcap record stream?
    print("  pcap magic? %s" % (d[:4] == b'\xd4\xc3\xb2\xa1'))
    # entropy + zero/ff ratio
    c = collections.Counter(d)
    z = c[0x00] / len(d)
    f = c[0xff] / len(d)
    nz = len(c)
    print("  distinct byte values %d, zeros %.1f%%, 0xff %.1f%%" % (nz, z * 100, f * 100))
    # printable density
    pr = sum(1 for x in d if 9 <= x < 127) / len(d)
    print("  printable %.1f%%" % (pr * 100))
    # search version strings
    for pat in (b'V3.', b'DS.', b'3.1.5', b'3.2.D', b'CR5', b'Dobot', b'boot'):
        i = d.find(pat)
        print("    %-8s %s" % (pat.decode(), ("0x%06x" % i) if i >= 0 else '-'))
