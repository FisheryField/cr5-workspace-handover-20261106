import struct
d = open(r"D:\mydata\workspace\data\Application.app",'rb').read()
N=len(d)
print("N=0x%x" % N)
for o in (0, 0x800, 0x1000, 0x10000, 0x5400):
    b=d[o:o+32]
    asc=''.join(chr(c) if 32<=c<127 else '.' for c in b)
    print("%08x  %-95s |%s|" % (o, b.hex(' '), asc))
print()
print("--- around anchor 0x5400 ---")
for o in range(0x53e0, 0x5430, 16):
    print("%08x  %s" % (o, d[o:o+16].hex(' ')))
print()
print("--- u32 table at 0x10000 ---")
for i in range(8):
    v,=struct.unpack_from("<I", d, 0x10000+i*4)
    print("  0x100%02x: 0x%08x %d" % (i*4, v, v))
print()
print("--- ascii string density map (1KB blocks with >50% printable) ---")
cnt=0
for i in range(0, N, 0x1000):
    blk=d[i:i+0x1000]
    if not blk: break
    pr=sum(1 for c in blk if 9<=c<127 or c==0)/len(blk)
    if pr>0.85:
        cnt+=1
print("  blocks >85%% printable: %d / %d" % (cnt, (N+0xfff)//0x1000))
print()
print("--- printable run boundaries (runs >= 64 chars) ---")
import re
for m in re.finditer(rb'[\x20-\x7e\t\n]{64,}', d):
    print("  off=0x%06x len=%d  %r" % (m.start(), m.end()-m.start(), d[m.start():m.start()+60]))
