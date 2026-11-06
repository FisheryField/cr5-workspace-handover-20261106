# -*- coding: utf-8 -*-
"""正确编码重读 real_gui_log.txt 的关键片段。"""
import io, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\glm-workplace\sim_scripts\real_gui_log.txt'
lines = io.open(P, encoding='utf-8', errors='replace').read().splitlines()
print('总行数 =', len(lines))

print('\n================ 16:51:15 ~ 16:51:40（单点 P1 + 导入11点）================')
for l in lines:
    if re.match(r'10-09 16:5[01]:', l):
        print(l)

print('\n================ 16:53:15 ~ 末（17点执行 → 停在 P1）================')
for l in lines:
    if re.match(r'10-09 16:53:', l):
        print(l)
