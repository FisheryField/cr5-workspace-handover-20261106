# -*- coding: utf-8 -*-
"""从解出的 .rdk 数据里抽取可读文本串，定位脚本/程序相关条目。"""
import re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
d = open(r'D:\mydata\workspace\_rdk_unpacked.bin', 'rb').read()

runs = []
for m in re.finditer(rb'[\x20-\x7e]{4,}', d):
    s = m.group().decode('ascii')
    runs.append((m.start(), s))
print('可读串总数 =', len(runs))

# 与脚本/文件路径相关的串
pat = re.compile(r'(?i)\.py|script|python|\.rdk|\.json|driver|程序|脚本')
print('\n--- 含 .py / script / python / driver 的串 ---')
hits = [(o, s) for o, s in runs if pat.search(s)]
for o, s in hits[:120]:
    print('%9d  %s' % (o, s[:200]))
print('命中数 =', len(hits))
