
import re, struct
P = r"D:\mydata\workspace\data\mToolServer.bin"
d = open(P,'rb').read()
print("=== 形如 URI 的字符串（>=6 字符，含 '/'，以 / 开头）===")
seen=[]
for m in re.finditer(rb'/[A-Za-z][A-Za-z0-9_/\.\-]{4,60}', d):
    s=m.group().decode('latin-1')
    if s.count('/')>=2 or s.startswith('/update') or s.startswith('/fault') or s.startswith('/protocol'):
        if s not in seen:
            seen.append(s); print("  0x%08x  %s" % (m.start(), s))
print("共 %d" % len(seen))
print()
print("=== HttpServer 相关符号 ===")
for m in re.finditer(rb'_ZN?K?10HttpServer[A-Za-z0-9_]*', d):
    s=m.group().decode('latin-1')
    if s not in [x for x in []]: pass
syms=set()
for m in re.finditer(rb'[A-Za-z0-9_]{6,200}', d):
    s=m.group().decode('latin-1')
    if 'HttpServer' in s: syms.add(s)
for s in sorted(syms): print("  ", s)
