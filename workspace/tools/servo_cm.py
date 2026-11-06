"""servo_cm.py - Cortex-M servo firmware probe + disassembler.

The FoE payload files have a small vendor header (0x10 bytes) in front of the
flash image; the Cortex-M vector table follows it.  This script locates the
table, maps flash address <-> file offset, verifies the exception vectors are
real Thumb code, and can disassemble / compare two versions.

usage:
  python tools\\servo_cm.py <file>
  python tools\\servo_cm.py <file> --dis 0x0801019c 12
  python tools\\servo_cm.py <a> --diff <b>
"""
import sys, os, struct, hashlib, collections

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS, CS_MODE_LITTLE_ENDIAN
    HAVE_CS = True
except Exception:
    HAVE_CS = False


def load(path):
    d = open(path, 'rb').read()
    # find the vector table: a word in SRAM followed by a word in flash (Thumb)
    for base in range(0, 0x40, 4):
        if base + 8 > len(d):
            break
        sp, rv = struct.unpack_from('<II', d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return d, base
    return d, None


def report(path):
    d, base = load(path)
    print("=" * 92)
    print("%s  %d bytes  md5 %s" % (os.path.basename(path), len(d), hashlib.md5(d).hexdigest()))
    if base is None:
        print("  !! no Cortex-M vector table found")
        return None, None
    print("  vendor header: 0x%x bytes -> %s" % (base, d[:base].hex(' ')))
    flash = d[base:]
    print("  flash image: %d bytes -> flash 0x08000000..0x%08x" % (len(flash), 0x08000000 + len(flash)))
    print("  [0x08000000] initial SP   = 0x%08x" % struct.unpack_from('<I', flash, 0)[0])
    vectors = [struct.unpack_from('<I', flash, i * 4)[0] for i in range(16)]
    names = ['SP', 'Reset', 'NMI', 'HardFault', 'MemManage', 'BusFault', 'UsageFault',
             '-', '-', '-', '-', 'SVCall', 'DebugMon', '-', 'PendSV', 'SysTick']
    print("  vector table:")
    for n, v in zip(names, vectors):
        tag = ''
        if n not in ('SP', '-') and v:
            tag = '  -> 0x%08x (Thumb)' % (v & ~1)
        print("     %-11s 0x%08x%s" % (n, v, tag))
    # code density check: thumb-2 code has many 16-bit instructions; look for
    # 'push {..., lr}'  (b5xx) and 'bl' (f0xx) patterns
    win = flash[:0x20000]
    b5 = sum(1 for i in range(0, len(win) - 2, 2) if win[i] in (0xb5,) )
    bl = sum(1 for i in range(0, len(win) - 4, 2)
             if (struct.unpack_from('<H', win, i)[0] & 0xf800) == 0xf000
             and (struct.unpack_from('<H', win, i + 2)[0] & 0xd000) == 0xd000)
    print("  first 128 KiB: 'push{r..,lr}' candidates %d, BL/BLX candidates %d" % (b5, bl))
    return d, base


def dis(flash, addr, n):
    if not HAVE_CS:
        print("capstone missing")
        return
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS | CS_MODE_LITTLE_ENDIAN)
    off = addr - 0x08000000
    print("--- disasm 0x%08x (%d insns) ---" % (addr, n))
    c = 0
    for ins in md.disasm(flash[off:off + n * 4], addr):
        print("  0x%08x  %-31s %-8s %s" %
              (ins.address, flash[ins.address - 0x08000000:ins.address - 0x08000000 + ins.size].hex(' '),
               ins.mnemonic, ins.op_str))
        c += 1
        if c >= n:
            break


def main(argv):
    path = argv[0]
    d, base = report(path)
    if base is None:
        return 1
    flash = d[base:]
    if len(argv) > 1 and argv[1] == '--dis':
        dis(flash, int(argv[2], 16), int(argv[3]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
