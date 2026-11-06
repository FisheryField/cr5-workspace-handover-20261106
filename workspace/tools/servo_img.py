#!/usr/bin/env python3
"""Shared loader for the servo firmware images.

IMPORTANT (cost a wrong result this session):
  These `.bin` files are the VENDOR PACKAGES, not raw flash dumps.  They begin
  with a ~0x20-byte FoE/vendor header, and the actual vector table (which maps
  to 0x08000000 in flash) is at file offset 0x20.

  Slicing `data[addr - 0x08000000:]` therefore disassembles shifted-by-0x20
  bytes.  The disassembly still "succeeds" (garbage decodes as valid Thumb), so
  the failure is SILENT: searches return 0 hits for instructions that are
  plainly visible in the output of tools that do handle the header.

  tools/thumb_dis.py already auto-detects the header by scanning the first
  0x40 bytes for a plausible Cortex-M vector table.  Reuse that logic here.

Always go through `load_image()`; never open these files directly.
"""
import struct

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN

FLASH_BASE = 0x08000000


def find_flash_start(d):
    """Return the file offset of the vector table == flash address 0x08000000."""
    for base in range(0, 0x40, 4):
        if len(d) < base + 8:
            break
        sp, rv = struct.unpack_from("<II", d, base)
        if 0x20000000 <= sp <= 0x20050000 and 0x08000000 <= (rv & ~1) < 0x08200000:
            return base
    raise SystemExit("no Cortex-M vector table found in image")


def load_image(path):
    """Return (data, flash_off, code) where code[i] corresponds to 0x08000000+i."""
    with open(path, "rb") as f:
        d = f.read()
    off = find_flash_start(d)
    return d, off, d[off:]


def slice_at(code, addr, size=None):
    """Slice the header-stripped image at a flash address."""
    o = addr - FLASH_BASE
    if o < 0:
        raise ValueError("address below flash base: 0x%08x" % addr)
    return code[o:] if size is None else code[o:o + size]


def make_md():
    """Capstone instance configured for WHOLE-IMAGE linear sweeps.

    skipdata is MANDATORY here.  Without it, `md.disasm(code, FLASH_BASE)` stops
    silently at the first undecodable bytes - in these images that is flash
    offset ~0xa60, i.e. after only ~1058 of ~151248 instructions (0.7%).

    Consequence (real, and it produced false "0 sites" results this session):
    a whole-image search built on plain disasm() only ever sees the first ~1 KB
    of code.  It reports 0 hits for instructions that plainly exist, and because
    the sweep "succeeded" nothing signals the truncation.

    For decoding ONE known-good region, plain disasm with a bounded slice is
    fine (servo_copyseq.py does that).
    """
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.skipdata = True
    return md
