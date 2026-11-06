
import re, json
d = open(r"D:\mydata\workspace\libdataSvr.so.bin",'rb').read()
# .rodata 0x1fdf08 size 262616, .data.rel.ro 0x266640, 以及字符串池区
cands=set()
for lo,hi in ((0x1fdf08,0x1fdf08+262616),(0x20b000,0x20c000),(0x218000,0x21a000)):
    for m in re.finditer(rb'[A-Za-z_][A-Za-z0-9_]{0,24}', d[lo:hi]):
        s=m.group().decode('latin-1')
        if 1<=len(s)<=24 and (s[0].islower() or s.isupper() or '_' in s):
            cands.add(s)
# 只保留看起来像 JSON 键的（纯标识符）
cands={c for c in cands if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', c)}
print("候选键 %d 个" % len(cands))
open(r"D:\mydata\workspace\data\key_cands.json","w").write(json.dumps(sorted(cands)))
print("样例:", sorted(cands)[:40])
