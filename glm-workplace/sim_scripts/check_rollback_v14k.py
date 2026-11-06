# -*- coding: utf-8 -*-
import ast, re
p = r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py'
src = open(p, encoding='utf-8').read()
ast.parse(src)
m = re.search(r"LOG_VERSION = '([^']+)'", src)
print('ast OK |', m.group(1), '|', len(src.encode('utf-8')), 'bytes')
# 回退目的核对：v14l 试航开关代码必须不存在
for kw in ('MOVL_TRIAL_MAX_MM', '_movl_trial_ready'):
    print(kw, 'present:', kw in src)
