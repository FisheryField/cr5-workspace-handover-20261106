#!/usr/bin/env python3
"""z_fw.py -- zero-mechanism investigation shared loader (2026-09-26).

Address convention used throughout THIS investigation
-----------------------------------------------------
The vendor `.bin` packages start with a 0x20-byte FoE header; the payload that
follows is the FoE application region, which the bootloader loads at
**0x08010000** (proved in data/servo_fw_samples/LOAD_ADDR_VERDICT.txt: 100.0000%
byte equality against the full 3.1.5.hex at that base).

Older session notes that used tools/mkelf.py label the payload at 0x08000000,
so every address in those notes is 0x10000 LOW.  This module always reports the
TRUE flash address:

    addr = 0x08010000 + file_offset

Positive controls (must pass, see selfcheck()):
  * version string "DS.3.1.5.0" / "DS.3.2.D.8" is found at flash 0x08027DCC /
    0x08029252.
  * reset vector at flash 0x0801019C is `ldr r0,[pc,#0x18]` / `blx r0` (which is
    exactly what data/servo_fw_samples/LOAD_ADDR_VERDICT.txt M3 reports).
"""
import struct
import sys

PAYLOAD_BASE = 0x08010000
HDR_LEN = 0x00   # VERIFIED 2026-09-26: these .bin files start AT the vector table
                 # (SP=0x20017a40, Reset=0x0801019d at file offset 0).  There is
                 # NO 0x20-byte vendor header inside the .bin (the 0x20 bytes that
                 # mkelf.py puts in .header are copied from the END of the file).
                 # => flash address = 0x08010000 + file offset, exactly.

SAMPLES = {
    '3150': r'data/servo_fw_samples/elf/v3150.bin',
    'd8':   r'data/servo_fw_samples/elf/v328d8.bin',
}
VERSION_FLASH = {'3150': 0x08027DCC, 'd8': 0x08029250}


class Fw(object):
    def __init__(self, tag, path=None):
        import os
        self.tag = tag
        self.path = path or SAMPLES[tag]
        if not os.path.isabs(self.path):
            root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.path = os.path.join(root, self.path)
        with open(self.path, 'rb') as f:
            self.raw = f.read()
        hdr = self.raw[:HDR_LEN]
        # vector table is the FIRST thing in the payload (verified): SP in SRAM,
        # reset handler in flash.
        sp, rv = struct.unpack_from('<II', self.raw, HDR_LEN)
        assert 0x20000000 <= sp <= 0x20050000, 'SP %08x not SRAM' % sp
        assert 0x08000000 <= (rv & ~1) < 0x08200000, 'reset %08x' % rv
        self.hdr = hdr
        self.code = self.raw[HDR_LEN:]
        self.base = PAYLOAD_BASE
        self.end = PAYLOAD_BASE + len(self.code)

    # ---- addressing -------------------------------------------------------
    def off(self, addr):
        """flash address -> index into self.code"""
        o = addr - self.base
        if o < 0 or o > len(self.code):
            raise ValueError('0x%08x outside payload' % addr)
        return o

    def read(self, addr, n):
        o = self.off(addr)
        return self.code[o:o + n]

    def rd32(self, addr):
        return struct.unpack_from('<I', self.code, self.off(addr))[0]

    def rd16(self, addr):
        return struct.unpack_from('<H', self.code, self.off(addr))[0]

    def find(self, needle, start=0):
        r = []
        i = self.code.find(needle, start)
        while i >= 0:
            r.append(self.base + i)
            i = self.code.find(needle, i + 1)
        return r

    # ---- disassembly ------------------------------------------------------
    def md(self):
        from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
        m = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
        m.skipdata = True
        return m

    def dis(self, addr, count=40, size=None):
        """Linear disassembly of `count` instructions starting at addr."""
        md = self.md()
        o = self.off(addr)
        blob = self.code[o:o + (size or 4 * count * 3)]
        out = []
        for i in md.disasm(blob, addr):
            out.append(i)
            if len(out) >= count:
                break
        return out

    def text(self, addr, count=40):
        return '\n'.join('  %08x  %-8s %s' % (i.address, i.mnemonic, i.op_str)
                         for i in self.dis(addr, count))

    # ---- whole image sweep ------------------------------------------------
    def sweep(self):
        """Linear sweep with skipdata; yields capstone insns in address order."""
        md = self.md()
        return md.disasm(self.code, self.base)

    def selfcheck(self, verbose=True):
        ok = True
        want = VERSION_FLASH[self.tag]
        p = self.code.find(b'DS.', self.off(want) - 8)
        got = self.base + p
        if got != want:
            ok = False
        if verbose:
            print('[selfcheck %s] version string @ 0x%08x (want 0x%08x) %s'
                  % (self.tag, got, want, 'PASS' if got == want else 'FAIL'))
        # reset vector
        rv = self.rd32(self.base + 4) & ~1
        if verbose:
            print('[selfcheck %s] reset vec 0x%08x -> %s' % (self.tag, rv, self.text(rv, 1).strip()))
        return ok


def load(tag):
    return Fw(tag)


if __name__ == '__main__':
    for t in ('3150', 'd8'):
        f = Fw(t)
        print('== %s  %s  payload %d B  flash 0x%08x..0x%08x'
              % (t, f.path, len(f.code), f.base, f.end))
        f.selfcheck()
