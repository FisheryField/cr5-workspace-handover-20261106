# -*- coding: utf-8 -*-
import io, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = r'D:\mydata\glm-workplace\sim_scripts\driver_timeout_probe.txt'
print('================ driver_timeout_probe.txt ================')
print(io.open(p, encoding='utf-8', errors='replace').read())

log = r'D:\mydata\glm-workplace\sim_scripts\real_gui_log.txt'
ls = io.open(log, encoding='utf-8', errors='replace').read().splitlines()
print('================ 15:58~16:01 的关键记录 ================')
keys = ('停止', '未到位', '版本', '分瓣', 'P1：', 'P2：', '【入口】', '实机当前关节')
for l in ls:
    if re.match(r'10-09 (15:5[89]|16:0[01])', l) and any(k in l for k in keys):
        print(l)
