"""Find OD-index literal words in both servo images: default PDO mapping tables,
SDO/OD index tables etc.  Positive controls built in.
true = ELF vaddr + 0x10000 ; ghidra = ELF vaddr
"""
import struct
ELF = {
    'v328d8': r'D:\mydata\workspace\data\servo_fw_samples\elf\v328d8.elf',
    'v3150':  r'D:\mydata\workspace\data\servo_fw_samples\elf\v3150.elf',
}
IDX = [0x607A, 0x6064, 0x6062, 0x6060, 0x6040, 0x6041, 0x6061, 0x606C, 0x6078,
       0x6098, 0x607C, 0x6091, 0x6092, 0x608F, 0x60FD, 0x1C12, 0x1C13, 0x1600, 0x1A00]
for name, path in ELF.items():
    d = open(path, 'rb').read()
    print('=' * 72); print(name, len(d))
    # --- positive control: version word at flash 0x0805F16C (true) ---
    t = 0x0805F16C - 0x10000 - 0x08000000 + 0x1000   # file offset
    print('  POSCTL version word @true 0x0805F16C: fileoff=0x%x val=0x%04x %s' %
          (t, struct.unpack_from('<H', d, t)[0], struct.unpack_from('<H', d, t)[0] in (0x32D8, 0x3150)))
    # --- scan for 32-bit words (idx<<16) and (idx) and 16-bit idx ---
    for kind, words in (('u32 idx<<16', [i << 16 for i in IDX]),
                        ('u32 idx', [i for i in IDX]),
                        ('u16 idx', [i for i in IDX])):
        print('  --- %s ---' % kind)
        for i in IDX:
            v = i << 16 if kind == 'u32 idx<<16' else i
            step, fmt = (4, '<I') if kind.startswith('u32') else (2, '<H')
            hits = []
            off = 0x1000
            end = len(d) - 4
            while off < end:
                if struct.unpack_from(fmt, d, off)[0] == v:
                    hits.append(off)
                off += step
            # cluster into tables (hits within 64 bytes of each other)
            tables = []
            for h in hits:
                if tables and h - tables[-1][-1] <= 64:
                    tables[-1].append(h)
                else:
                    tables.append([h])
            if hits:
                desc = ', '.join('n=%d @true %08x' % (len(tb), tb[0] - 0x1000 + 0x08010000)
                                 for tb in tables)
                print('    0x%04x: %d hits; %s' % (i, len(hits), desc))
    # --- dump around the big candidate tables (>=4 distinct hits close together) ---
    print('  --- table dumps (any 6 consecutive 4-byte words whose high half is 0x60xx/0x1Cxx/0x1Axx) ---')
    off = 0x1000
    n = 0
    while off < len(d) - 24 and n < 12:
        ok = True
        for k in range(6):
            w = struct.unpack_from('<I', d, off + 4 * k)[0]
            hi = w >> 16
            if not (0x6000 <= hi <= 0x60FF or 0x1C00 <= hi <= 0x1CFF or 0x1A00 <= hi <= 0x1AFF):
                ok = False; break
        if ok:
            n += 1
            print('    TABLE? true=%08x' % (off - 0x1000 + 0x08010000))
            for k in range(8):
                w = struct.unpack_from('<I', d, off + 4 * k)[0]
                print('        true=%08x  0x%08x   (hi=0x%04x lo=0x%04x)' %
                      (off + 4 * k - 0x1000 + 0x08010000, w, w >> 16, w & 0xffff))
            off += 4
        off += 4
    print('  total table-like regions printed:', n)
