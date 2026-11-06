"""servo_od_service.py - map and size the object-dictionary access service of the servo
image (the code that materialises CiA402 indices).

Established with tools/servo_cia402_refs.py + tools/thumb_dis.py:

  0x0800289C  OD access service entry
                r3 = 0x800 ; r3 = r1 - 0x800*r2      (r1=index, r2=subindex)
                then a binary-search compare chain on CiA402 indices:
                  0x608E, 0x6072, 0x6064, 0x605C, 0x6041, 0x6007.., with a
                  `tbb [pc,r3]` / `tbh [pc,r3,lsl#1]` jump table
  0x08002BBC  0x6064 (Position Actual Value) handler:
                r3 = r2 * 0x329 ; r3 += [0x2000138C] ; r3 += field_offset
                str r3,[r0,#0x18]        -> hands back a pointer to the object slot
                So object descriptors live in an array with STRIDE 0x329, and the
                CiA402 field offset (0x18, 0x238, 0x23c, ...) selects the member.

This script:
  * walks the dispatch chain from the entry and collects every CiA402 index constant
    the chain compares against, in program order (i.e. the real object list)
  * resolves each compare's branch target (the handler)
  * measures the span of the service and prints a size estimate, so coverage can be
    reported honestly

usage:
  python tools\\servo_od_service.py <flash.bin> [--entry 0x0800289c] [--len 0x600]
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
    entry = int(argv[argv.index('--entry') + 1], 16) if '--entry' in argv else 0x0800289c
    ln = int(argv[argv.index('--len') + 1], 16) if '--len' in argv else 0x600

    print("OD access service from 0x%08x, scanning 0x%x bytes" % (entry, ln))

    # collect the compare chain: movw rN,#idx followed within 3 insns by a branch
    listing = list(md.disasm(flash[entry - FLASH_BASE:entry - FLASH_BASE + ln], entry))
    chain = []
    for i, ins in enumerate(listing):
        if ins.mnemonic == 'movw':
            try:
                v = int(ins.op_str.split('#')[1], 0)
            except (IndexError, ValueError):
                continue
            if 0x6000 <= v <= 0x6100:
                # find the next branch and its target
                tgt = None
                for j in range(i + 1, min(i + 8, len(listing))):
                    nx = listing[j]
                    if nx.mnemonic in ('beq', 'bne', 'b', 'bgt', 'blt', 'bge', 'ble', 'bhs', 'blo'):
                        if nx.op_str.startswith('#'):
                            try:
                                tgt = int(nx.op_str[1:], 0) & ~1
                            except ValueError:
                                tgt = None
                        break
                chain.append((ins.address, v, tgt))

    print("\n=== CiA402 index compare chain (program order) ===")
    print("  %-10s %-8s %s" % ("at", "index", "handler"))
    for a, v, t in chain:
        print("  0x%08x 0x%04X   %s" % (a, v, ('0x%08x' % t) if t else '?'))

    idxs = [v for _a, v, _t in chain]
    print("\n  %d index constant(s) in the chain" % len(idxs))
    if idxs:
        print("  span 0x%04X..0x%04X" % (min(idxs), max(idxs)))

    # stride check: find muls by 0x329 in the handler region
    print("\n=== object-array stride uses (muls rN, rM, #0x329) ===")
    n = 0
    for ins in md.disasm(flash[entry - FLASH_BASE:entry - FLASH_BASE + 0x900], entry):
        if ins.mnemonic in ('muls', 'mul', 'mla') and '0x329' in ins.op_str:
            if n < 12:
                print("  0x%08x  %s %s" % (ins.address, ins.mnemonic, ins.op_str))
            n += 1
    print("  %d site(s) in this region" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
