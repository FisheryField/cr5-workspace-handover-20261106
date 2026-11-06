# -*- coding: utf-8 -*-
import difflib, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
a = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read().splitlines()          # v14k
b = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版_v14l_20261012-1117.py.bak', encoding='utf-8').read().splitlines()  # v14l
d = list(difflib.unified_diff(a, b, fromfile='v14k', tofile='v14l', lineterm='', n=2))
print('diff lines total:', len(d))
# 输出全部变更块，压缩空行
buf = []
for l in d:
    buf.append(l)
out = '\n'.join(buf)
open(r'D:\mydata\glm-workplace\sim_scripts\diff_v14k_v14l.txt', 'w', encoding='utf-8').write(out)
print('written diff_v14k_v14l.txt')
# 统计变更块
hunks = [l for l in d if l.startswith('@@')]
print('hunks:', len(hunks))
for h in hunks:
    print(' ', h)
