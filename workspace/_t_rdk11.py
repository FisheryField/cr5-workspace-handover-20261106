# -*- coding: utf-8 -*-
"""把脚本条目名前后的二进制结构（类型码/图标/路径/长度）解出来，搞清"引用还是内嵌"。"""
import re, struct, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

d = open(r'D:\mydata\workspace\_rdk_unpacked.bin', 'rb').read()
names = ['TCP真实运动_升级前备份_20260910_170410', 'TCP仿真', 'test',
         '机械臂法兰真实运动', 'TCP真实运动_到位复核前备份_20260910_172919',
         'TCP真实运动_旧版_20261009_113434', 'TCP仿真_退让换向升级前',
         'TCP真实运动_升级前备份_20261009_113242', 'TCP真实运动']

for nm in names:
    b = nm.encode('utf-16-le')
    i = d.find(b)
    if i < 0:
        print('%-45s 未找到' % nm); continue
    ln = struct.unpack_from('<H', d, i-2)[0]
    print('\n=== %s  @%d  (len字段=%d) ===' % (nm, i, ln))
    print('  名字前 48 B  hex:', d[i-48:i].hex(' '))
    print('  名字字段      :', d[i-2:i+len(b)].hex(' '))
    print('  名字后 96 B  hex:', d[i+len(b):i+len(b)+96].hex(' '))
    print('  名字后 96 B  txt:', ''.join(chr(c) if 32 <= c < 127 else '.' for c in d[i+len(b):i+len(b)+96]))
