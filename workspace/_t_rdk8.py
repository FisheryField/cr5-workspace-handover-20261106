# -*- coding: utf-8 -*-
"""抽取 .rdk 内每个脚本条目的 UTF-16 名字与日期戳，并算出代码块 sha 便于比对。"""
import hashlib, os, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

d = open(r'D:\mydata\workspace\_rdk_unpacked.bin', 'rb').read()
offs = [663, 1861423, 1910630, 1959618, 2013647, 2050611, 2125607,
        2179227, 2233776, 2290613, 2355833, 2410523, 2473317]

def u16_runs(b, minlen=2):
    """从字节串里抽出 UTF-16LE 可读串。"""
    out = []
    for m in re.finditer((rb'(?:[\x20-\x7e\u0080-\uffff]\x00){%d,}' % minlen), b):
        pass
    return out

def utf16_names(blob):
    """扫描 UTF-16LE 文本：取 '[\x20-\xff]\x00' 连续段并解码。"""
    names, cur = [], bytearray()
    i = 0
    while i + 1 < len(blob):
        lo, hi = blob[i], blob[i+1]
        if hi == 0 and lo >= 0x20:
            cur.append(lo); cur.append(0); i += 2
        elif lo == 0 and hi >= 0x20 and hi < 0x80 and 0:
            cur.append(lo); cur.append(hi); i += 2
        else:
            if len(cur) >= 6:
                try:
                    names.append(cur.decode('utf-16-le'))
                except UnicodeDecodeError:
                    pass
            cur = bytearray(); i += 1
    if len(cur) >= 6:
        try: names.append(cur.decode('utf-16-le'))
        except UnicodeDecodeError: pass
    return names

print('=== 每个条目代码块前 500 B 内的 UTF-16 文本 ===')
for i, o in enumerate(offs):
    print('\n--- 块 %02d @%d ---' % (i, o))
    before = d[max(0, o-500):o]
    for s in utf16_names(before):
        if len(s.strip()) >= 3:
            print('   [前] %r' % s)
    nxt = offs[i+1] if i+1 < len(offs) else len(d)
    seg = d[o:o+1200]
    # 代码结束：第一个 \x00 且其后不是明文 python 的地方
    end = seg.find(b'\x00')
    after = d[o+end:o+end+400] if end >= 0 else b''
    for s in utf16_names(after):
        if len(s.strip()) >= 3:
            print('   [后] %r' % s)

print('\n=== 全站 UTF-16 名字表（含 .py 的）===')
for s in set(utf16_names(d)):
    if '.py' in s or '20260' in s or 'TCP' in s or '法兰' in s or '仿真' in s:
        print('   %r  (出现 %d 次)' % (s, d.count(s.encode('utf-16-le'))))
