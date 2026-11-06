# -*- coding: utf-8 -*-
"""精确抽取 .rdk 内 13 个脚本条目的名字（长度前缀 UTF-16）+ 代码 sha，并与磁盘比对。"""
import hashlib, os, re, struct, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

d = open(r'D:\mydata\workspace\_rdk_unpacked.bin', 'rb').read()
offs = [663, 1861423, 1910630, 1959618, 2013647, 2050611, 2125607,
        2179227, 2233776, 2290613, 2355833, 2410523, 2473317]
D = r'D:\mydata\working things\dobot_arm\RoboDK files 2'
disk = {}
for dirpath, dirs, files in os.walk(r'D:\mydata'):
    if any(x in dirpath for x in ('node_modules', 'pythoncore', '.pylibs', 'site-packages', '\\Python\\')):
        continue
    for fn in files:
        if fn.lower().endswith('.py'):
            p = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(p) >= 2000:
                    disk[p] = open(p, 'rb').read()
            except OSError:
                pass
print('磁盘候选 .py =', len(disk))

def name_of(o):
    """代码块前的条目名：形如 <2B len><UTF16>，往前再取若干段。"""
    parts = []
    pos = o
    for _ in range(6):
        # 往前找 (len, utf16) 结构：先假设名字紧随代码前
        for back in range(2, 260):
            s = pos - back
            if s < 0:
                break
            ln = struct.unpack_from('<H', d, s)[0]
            if ln and ln * 2 == back - 2 and ln >= 3:
                try:
                    txt = d[s+2:s+2+ln*2].decode('utf-16-le')
                except UnicodeDecodeError:
                    continue
                if all(0x20 <= ord(c) or c in '\r\n' for c in txt):
                    parts.append(txt)
                    pos = s
                    break
        else:
            break
    return parts

for i, o in enumerate(offs):
    nxt = offs[i+1] if i+1 < len(offs) else len(d)
    seg = d[o:nxt]
    # 代码结束：找 \x00 之前最后一个完整 utf-8 前缀
    try:
        seg.decode('utf-8'); end = len(seg)
    except UnicodeDecodeError as e:
        end = e.start
    code = seg[:end]
    h = hashlib.sha256(code).hexdigest()
    names = name_of(o)
    print('\n块 %02d  @%-8d code=%7d B  sha=%s' % (i, o, len(code), h[:16]))
    for nm in names:
        print('     名字段: %r' % nm)
    for p, raw in disk.items():
        if raw == code:
            print('     ✔ 与磁盘【%s】逐字节相同' % p)
        elif raw.replace(b'\r\n', b'\n') == code.replace(b'\r\n', b'\n'):
            print('     ≈ 仅换行差异【%s】' % p)
