
import re
d = open(r"D:\mydata\workspace\data\mToolServer.bin",'rb').read()
for key in (b'singleFwAndXml', b'fault/check', b'protocol/version'):
    i = d.find(key)
    print("### %s @ 0x%x" % (key.decode(), i if i>=0 else -1))
    if i<0: continue
    seg = d[max(0,i-700): i+700]
    for m in re.finditer(rb'[\x20-\x7e]{3,80}', seg):
        off = max(0,i-700)+m.start()
        print("   0x%08x  %r" % (off, m.group().decode('latin-1')))
    print()
print("=== 所有 HttpServer 符号 ===")
syms=set()
for m in re.finditer(rb'[A-Za-z0-9_]{8,220}', d):
    s=m.group().decode('latin-1')
    if 'HttpServer' in s: syms.add(s)
for s in sorted(syms): print("  ", s)
