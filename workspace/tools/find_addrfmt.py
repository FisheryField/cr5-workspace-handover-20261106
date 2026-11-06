
import struct,re
P = r"D:\mydata\workspace\libdataSvr.so.bin"
d = open(P,'rb').read()
pats = [b'addr%x', b'%x0%d', b'%x%d', b'H%02d', b'H0%d', b'pack addr', b'GetIndexFromAddr', b'AddrFromIndex', b'#%d', b'%d.%d', b'%02d.%02d', b'H', b'ParaMapIndex', b'ParaIndex']
def a2o(addr):
    return None
# 直接全文件扫可见字符串，过滤关键词
seen=set()
res=[]
for m in re.finditer(rb'[\x20-\x7e]{3,120}', d):
    s=m.group()
    if any(k in s for k in (b'addr%', b'%x0%d', b'%x%d', b'pack addr', b'.%d', b'H%0', b'H%d')):
        res.append((m.start(), s))
for off,s in res[:60]:
    print("  off=0x%08x  %r" % (off, s.decode('latin-1')))
print()
print("=== 邻近 'pack addr' 的字符串组 ===")
i = d.find(b'pack addr')
print("  pack addr off = 0x%x" % i)
seg = d[i-400:i+700]
for m in re.finditer(rb'[\x20-\x7e]{2,120}', seg):
    print("    0x%08x  %r" % (i-400+m.start(), m.group().decode('latin-1')))
