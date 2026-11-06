# -*- coding: utf-8 -*-
"""在解出的 .rdk 里定位每个内嵌 python 源码块的边界，取 SHA-256，并与磁盘文件比对。"""
import hashlib, os, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

d = open(r'D:\mydata\workspace\_rdk_unpacked.bin', 'rb').read()
D = r'D:\mydata\working things\dobot_arm\RoboDK files 2'

# 1) 找所有 "#!" shebang 起点
starts = [m.start() for m in re.finditer(rb'#!\[?/?usr/bin/env|#!/usr/bin', d)]
print('shebang 起点数 =', len(starts), starts[:20])

# 2) 找所有内嵌 import robodk 的起点（有些脚本可能没 shebang）
starts2 = [m.start() for m in re.finditer(rb'from robodk\.robolink import \*', d)]
print('from robodk.robolink import * 出现 =', len(starts2), starts2[:30])

# 3) 在磁盘上找所有 .py 候选
disk = {}
for dirpath, dirs, files in os.walk(r'D:\mydata'):
    if any(x in dirpath for x in ('\\.git', 'node_modules', 'pythoncore', '.pylibs', 'site-packages')):
        continue
    for fn in files:
        if fn.lower().endswith('.py'):
            p = os.path.join(dirpath, fn)
            try:
                st = os.stat(p)
                if st.st_size < 2000:
                    continue
                disk[p] = st.st_size
            except OSError:
                pass
print('\n磁盘上 >=2000B 的 .py 数 =', len(disk))

# 4) 对每个 shebang 起点，测多种结束符，取能匹配到磁盘文件的最长块
END_PATS = [b'\x00', b'\r\n\r\n\r\n', b'\n\n\n\n', b'\x00\x00']
results = []
for s in starts:
    best = None
    for pat in END_PATS:
        e = d.find(pat, s)
        if e < 0:
            continue
        blob = d[s:e]
        try:
            blob.decode('utf-8')
        except UnicodeDecodeError:
            continue
        h = hashlib.sha256(blob).hexdigest()
        results.append((s, e, len(blob), pat, h))
        if best is None or len(blob) > best[2]:
            best = (s, e, len(blob), pat, h)
    if best:
        s0, e0, ln, pat, h = best
        match = [p for p, sz in disk.items() if sz == ln]
        print('\n@%d..%d len=%d end=%r sha256=%s' % (s0, e0, ln, pat, h[:16]))
        print('   首行:', d[s0:s0+120].decode('utf-8', 'replace').splitlines()[0])
        for p in match[:6]:
            print('   磁盘同尺寸候选: %s' % p)

# 5) 直接对磁盘上所有候选 .py 算 sha，看哪些出现在 .rdk 解压体里
print('\n=== 磁盘 .py 是否逐字节出现在 .rdk 内 ===')
for p, sz in sorted(disk.items(), key=lambda kv: -kv[1])[:40]:
    raw = open(p, 'rb').read()
    if raw in d:
        print('  [整文件命中] %8d  %s' % (sz, p))
    else:
        # 试去掉 CRLF
        if raw.replace(b'\r\n', b'\n') in d:
            print('  [LF化后命中] %8d  %s' % (sz, p))
