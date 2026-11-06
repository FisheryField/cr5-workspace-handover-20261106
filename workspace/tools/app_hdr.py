
import struct
d = open(r"D:\mydata\workspace\data\Application.app",'rb').read()
N=len(d)
print("文件大小 = %d (0x%x)" % (N,N))
print("=== 头 256 字节 ===")
for o in range(0,256,16):
    b=d[o:o+16]
    asc=''.join(chr(c) if 32<=c<127 else '.' for c in b)
    print("  %04x  %-47s  %s" % (o, b.hex(' '), asc))
print()
print("=== 头里出现的 uint32 (前 32 个) ===")
for i in range(32):
    v,=struct.unpack_from("<I", d, i*4)
    note=""
    if 0 < v < N: note=" <== 落在文件内(可能是偏移)"
    if 0x00800000 <= v < 0x00900000: note=" <== 像是 0x80xxxx 基址指针"
    print("   [%2d] off=%3d  0x%08x  %d%s" % (i, i*4, v, v, note))
print()
print("=== 搜 'Application' 若干次出现 ===")
import re
for m in list(re.finditer(rb'Application', d))[:8]:
    print("   0x%06x  %r" % (m.start(), d[m.start()-8:m.start()+20]))
print()
print("=== 找可能的段表: 连续 uint32 且都 < 文件大小 ===")
best=None
for start in range(0, 0x400, 4):
    cnt=0; p=start
    while p+4<=N:
        v,=struct.unpack_from("<I", d, p)
        if v==0: break
        if v>=N: break
        cnt+=1; p+=4
        if cnt>20: break
    if best is None or cnt>best[1]: best=(start,cnt)
print("   最佳起点 off=0x%x, 连续 %d 个" % best)
if best[1]>=4:
    s=best[0]
    for i in range(min(best[1],16)):
        v,=struct.unpack_from("<I", d, s+i*4)
        print("      [%d] 0x%08x (%d)" % (i, v, v))
