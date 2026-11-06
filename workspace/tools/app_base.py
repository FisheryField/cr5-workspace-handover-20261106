
import struct
d = open(r"D:\mydata\workspace\data\Application.app",'rb').read()
N = len(d)
print("文件大小 0x%x (%d)" % (N, N))
known = {
  'a1.config.write': 0x0e9f08,
  'a1.config.read' : 0x0ebd18,
  'a1.write'       : 0x0eac60,
  'a1.read'        : 0x0eca22,
  'Application(hdr)': 0x000008,
}
# 对每个已知偏移，找低 12 位一致的 dword
for name, off in known.items():
    lo12 = off & 0xFFF
    hits=[]
    for i in range(0, N-4, 2):
        v,=struct.unpack_from("<I", d, i)
        if v < 0x00100000 or v > 0x80000000: continue
        if (v & 0xFFF) != lo12: continue
        B = v - off
        hits.append((i, v, B))
    print()
    print("## %s  文件偏移=0x%x  低12位=0x%x  命中 %d" % (name, off, lo12, len(hits)))
    for i,v,B in hits[:10]:
        print("    池@0x%06x  值=0x%08x  => 推测基址 B=0x%08x" % (i,v,B))
# 统计最常见的 dword 高位分布，找 B 的线索
from collections import Counter
c = Counter()
for i in range(0, N-4, 4):
    v,=struct.unpack_from("<I", d, i)
    if 0x00100000 <= v <= 0x80000000:
        c[v & 0xFFF00000] += 1
print()
print("=== 高 12 位分布 (top 12) ===")
for k,n in c.most_common(12):
    print("   0x%08x  x%d" % (k, n))
