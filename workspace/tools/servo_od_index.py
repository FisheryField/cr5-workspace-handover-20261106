#!/usr/bin/env python3
"""Parse the servo OD metadata table and, where possible, recover each entry's
CiA402 index — then line it up with the dispatcher's index set.

The known table layout (from earlier rounds):
    flash 0x08024991 .. 0x0802642e, 97 records
    record = name\0 + u16 type + u16 bits + u16 attr
Earlier rounds recorded "the table carries no index", which is why index->name
attribution was never done.  Re-check that here rather than trusting it: scan
the bytes immediately preceding each name for a plausible 16-bit index in the
0x1000..0x7FFF range.
"""
import sys

sys.path.insert(0, "tools")

from servo_img import FLASH_BASE, load_image

TYPES = {0x02: "i8", 0x03: "i16", 0x04: "i32", 0x05: "u8", 0x06: "u16", 0x07: "u32"}

CASES = [("D8", "data/servo_fw_samples/elf/v328d8.bin"),
         ("3150", "data/servo_fw_samples/elf/v3150.bin")]


def cstr(code, o):
    e = code.find(b"\x00", o)
    if e < 0:
        return None, o
    try:
        return code[o:e].decode("ascii"), e + 1
    except UnicodeDecodeError:
        return None, o


for label, path in CASES:
    _r, _h, code = load_image(path)
    start, end = 0x08024991 - FLASH_BASE, 0x0802642E - FLASH_BASE
    print("=" * 74)
    print("BUILD %s : OD table 0x%08x..0x%08x" % (label, start + FLASH_BASE, end + FLASH_BASE))
    print("=" * 74)

    recs = []
    o = start
    while o < end:
        name, after = cstr(code, o)
        if not name or len(name) < 3:
            o += 1
            continue
        if after + 6 > len(code):
            break
        type_, bits, attr = (int.from_bytes(code[after:after + 2], "little"),
                             int.from_bytes(code[after + 2:after + 4], "little"),
                             int.from_bytes(code[after + 4:after + 6], "little"))
        if type_ in TYPES and bits in (8, 16, 32):
            # look back up to 8 bytes for a candidate 16-bit index
            cand = None
            for back in range(2, 9, 2):
                v = int.from_bytes(code[o - back:o - back + 2], "little")
                if 0x1000 <= v <= 0x7FFF:
                    cand = v
                    break
            recs.append((o + FLASH_BASE, name, type_, bits, attr, cand))
            o = after + 6
        else:
            o += 1

    print("records parsed: %d" % len(recs))
    indexed = [r for r in recs if r[5] is not None]
    print("records with a plausible index in the preceding bytes: %d" % len(indexed))
    print()
    print("  addr        index   name")
    for a, name, t, b, attr, cand in recs:
        tag = "0x%04X" % cand if cand is not None else "  --  "
        print("  %08x  %s  %s" % (a, tag, name))
    print()
