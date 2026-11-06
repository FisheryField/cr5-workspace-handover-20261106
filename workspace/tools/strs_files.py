
import re
d = open(r"D:\mydata\workspace\libdataSvr.so.bin",'rb').read()
print("=== 所有 'files\\x00' 出现处及其邻域 ===")
for m in re.finditer(rb'files\x00', d):
    o=m.start()
    lo=max(0,o-160); hi=o+160
    print("--- 0x%06x ---" % o)
    for x in re.finditer(rb'[\x20-\x7e]{1,80}', d[lo:hi]):
        print("   0x%06x  %r" % (lo+x.start(), x.group().decode('latin-1')))
    print()
print("=== .rodata 里 1~4 字符的短字符串（可能是成员名）===")
# .rodata 0x1fdf08..0x20df00
seen=[]
for m in re.finditer(rb'[a-zA-Z_][a-zA-Z0-9_]{0,12}\x00', d[0x1fdf08:0x20df00]):
    s=m.group()[:-1].decode('latin-1')
    seen.append((0x1fdf08+m.start(), s))
for a,s in seen[:60]:
    print("   0x%06x  %r" % (a,s))
print("   共 %d 个" % len(seen))
