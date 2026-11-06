
import re
d = open(r"D:\mydata\workspace\libdataSvr.so.bin",'rb').read()
i = d.find(b'/dobot/userdata/project/settings/function/servoParams.json')
print("servoParams.json 路径 @0x%x" % i)
lo, hi = i-0x260, i+0x140
print("=== 0x%x .. 0x%x 的字符串池 ===" % (lo,hi))
for m in re.finditer(rb'[\x20-\x7e]{2,120}', d[lo:hi]):
    print("   0x%06x  %r" % (lo+m.start(), m.group().decode('latin-1')))
print()
j = d.find(b'IsWriteFromFile')
print("IsWriteFromFile @0x%x" % j)
lo2, hi2 = j-0x300, j+0x180
print("=== 0x%x .. 0x%x ===" % (lo2,hi2))
for m in re.finditer(rb'[\x20-\x7e]{2,120}', d[lo2:hi2]):
    print("   0x%06x  %r" % (lo2+m.start(), m.group().decode('latin-1')))
