# -*- coding: utf-8 -*-
"""线性版：解析 .rdk 内嵌脚本条的头部元数据 + 代码块边界。"""
import hashlib, os, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

d = open(r'D:\mydata\workspace\_rdk_unpacked.bin', 'rb').read()
print('头部前 80 字节 repr:', repr(d[:80]))

offs = [663, 1861423, 1910630, 1959618, 2013647, 2050611, 2125607,
        2179227, 2233776, 2290613, 2355833, 2410523, 2473317]
D = r'D:\mydata\working things\dobot_arm\RoboDK files 2'
refs = {}
for fn in os.listdir(D):
    p = os.path.join(D, fn)
    if os.path.isfile(p) and fn.lower().endswith('.py'):
        refs[fn] = open(p, 'rb').read()

def longest_utf8(b):
    """线性求能被 utf-8 解码的最长前缀长度。"""
    try:
        b.decode('utf-8')
        return len(b)
    except UnicodeDecodeError as e:
        return e.start

for i, o in enumerate(offs):
    nxt = offs[i+1] if i+1 < len(offs) else len(d)
    seg = d[o:nxt]
    end = longest_utf8(seg)
    code = seg[:end]
    print('\n############ 块 %02d @%d' % (i, o))
    print('  头部 RAW[-260:0] =', repr(d[max(0, o-260):o])[-400:])
    print('  代码 %d B  sha=%s  首行=%r' % (len(code), hashlib.sha256(code).hexdigest()[:16], code.split(b'\r\n')[0][:80]))
    for fn, raw in refs.items():
        if raw == code:
            print('  ✔ 逐字节 == 磁盘【%s】' % fn)
        elif raw.replace(b'\r\n', b'\n') == code.replace(b'\r\n', b'\n'):
            print('  ≈ 仅换行差异 == 磁盘【%s】' % fn)
    print('  代码后 RAW =', repr(seg[end:end+220]))
