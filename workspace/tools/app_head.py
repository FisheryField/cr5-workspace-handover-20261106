import struct, hashlib, re
d = open(r"D:\mydata\workspace\data\Application.app",'rb').read()
N=len(d)
print("N = 0x%x (%d)" % (N,N))
print("=== first 0x400 bytes, hex+ascii ===")
for o in range(0, 0x400, 16):
    b=d[o:o+16]
    asc=''.join(chr(c) if 32<=c<127 else '.' for c in b)
    print("  %08x  %-47s  |%s|" % (o, b.hex(' '), asc))
print()
print("=== u32 view of the first 0x100 bytes ===")
for i in range(0, 0x100, 4):
    v,=struct.unpack_from("<I", d, i)
    print("  +%03x  0x%08x  %d" % (i, v, v))
print()
print("=== strings near the start (>= 6 chars) ===")
for m in list(re.finditer(rb'[\x20-\x7e]{6,}', d[:0x2000])):
    print("   0x%06x %r" % (m.start(), m.group()))
print()
print("=== how many places look like the relocation placeholder 0x0004xxxx low16 ===")
# from the observed diffs: file word low16 = 0x01a0 / 0x04a8 for target 0x75a97484
# so target = base + (index-1)*0x10000 + value
print("  (checking at 0x1258: file word=%r  mem word=%r)" %
      (d[0x1258:0x125c].hex(' '), None))
print("  file 0x1258 dword = 0x%08x" % struct.unpack_from("<I", d, 0x1258)[0])
print("  file 0x1550 dword = 0x%08x" % struct.unpack_from("<I", d, 0x1550)[0])
print("  file 0x1554 dword = 0x%08x" % struct.unpack_from("<I", d, 0x1554)[0])
print()
print("=== count of dwords in 0x00000000..0x00010000 range per 64K block ===")
for blk in range(0, N, 0x10000):
    n=0
    for i in range(blk, min(blk+0x10000, N-4), 4):
        v,=struct.unpack_from("<I", d, i)
        if 0x00000000 <= v < 0x01000000:
            n+=1
    print("  0x%06x  %d" % (blk, n))
