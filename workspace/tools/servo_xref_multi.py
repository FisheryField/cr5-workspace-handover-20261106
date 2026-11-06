"""servo_xref_multi.py - find callers of several targets in one pass over an image.

Passing each address to a separate scan is wasteful and, more importantly, makes it
easy to miss callers that reach a routine through a different instruction form.
This walks the image once, decodes every 2-byte offset, and reports all branch /
call sites whose computed target matches any requested address (bit0 masked, so
Thumb state bits and ARM/Thumb interworking forms are both covered).

usage:
  python tools\\servo_xref_multi.py <flash.bin> 0x080017d0 0x08001810 ...
  python tools\\servo_xref_multi.py <flash.bin> --region 0x08051b00 0x08052000
"""
import sys, struct

FLASH_BASE = 0x08000000


def load(path):
    d = open(path, 'rb').read()
    for base in range(0, 0x40, 4):
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base, d[base:]
    raise SystemExit("no vector table in %s" % path)


def main(argv):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)

    path = argv[0]
    flash, _b, _f = load(path)

    targets = set()
    if '--region' in argv:
        lo = int(argv[argv.index('--region') + 1], 16)
        hi = int(argv[argv.index('--region') + 2], 16)
        targets = set(range(lo, hi, 2))
    else:
        targets = {int(x, 16) & ~1 for x in argv[1:] if x.startswith('0x')}

    print("image %s (%d B)" % (path, len(flash)))
    print("looking for branches to %d target(s)%s" %
          (len(targets), "" if len(targets) < 20 else " (region mode)"))

    # collect every pointer-like dword too, so tables are not mistaken for calls
    ptr_sites = {}
    for o in range(0, len(flash) - 4, 4):
        v = struct.unpack_from('<I', flash, o)[0]
        if (v & ~1) in targets:
            ptr_sites.setdefault(v & ~1, []).append(FLASH_BASE + o)

    branch_sites = {}
    a = FLASH_BASE
    end = FLASH_BASE + len(flash) - 4
    while a <= end:
        for i in md.disasm(flash[a - FLASH_BASE:a - FLASH_BASE + 4], a):
            mn = i.mnemonic
            if mn in ('bl', 'blx', 'b', 'b.w', 'bx') and i.op_str.startswith('#'):
                try:
                    t = int(i.op_str[1:], 0) & ~1
                except ValueError:
                    break
                if t in targets:
                    branch_sites.setdefault(t, []).append((i.address, mn))
            break
        a += 2

    print("\n=== branch/call sites ===")
    if not branch_sites:
        print("  none")
    for t in sorted(branch_sites):
        sites = branch_sites[t]
        print("  0x%08x : %d site(s)" % (t, len(sites)))
        for a2, mn in sites[:20]:
            print("      0x%08x  %s" % (a2, mn))
        if len(sites) > 20:
            print("      ... (%d more)" % (len(sites) - 20))

    print("\n=== data dwords (4-byte aligned) holding the same targets ===")
    if not ptr_sites:
        print("  none")
    for t in sorted(ptr_sites):
        sites = ptr_sites[t]
        print("  0x%08x : %d dword site(s): %s" %
              (t, len(sites), ' '.join('0x%08x' % s for s in sites[:12])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
