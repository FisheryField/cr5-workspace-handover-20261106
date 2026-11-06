# -*- coding: utf-8 -*-
"""解出 .rdk 本体到工作区，并分析 Python 脚本在站内的存法。"""
import io, os, re, struct, sys, zlib

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\working things\dobot_arm\RoboDK files 2\2026-9-7.rdk'
OUT = r'D:\mydata\workspace\_rdk_unpacked.bin'
raw = open(P, 'rb').read()
size = struct.unpack_from('>I', raw, 0)[0]
d = zlib.decompress(raw[4:])
print('声明未压缩长度 =', size, ' 实际 =', len(d), ' 一致 =', size == len(d))
open(OUT, 'wb').write(d)
print('已写出', OUT)

head = d[:200]
print('\n--- 前 200 字节 ascii ---')
print(''.join(chr(c) if 32 <= c < 127 else '.' for c in head))

txt = d.decode('utf-8', 'replace')
print('\n--- 长度(字符) =', len(txt))

# 关键：找脚本相关键名
for kw in ['Script', 'script', 'Python', 'python', '.py', 'pyfile', 'Program', 'Driver']:
    n = txt.count(kw)
    print('关键词 %-9s 出现 %d 次' % (kw, n))
