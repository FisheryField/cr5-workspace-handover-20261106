# -*- coding: utf-8 -*-
"""对比 %TEMP%\TCP真实运动2.py（实际运行副本）与站内活动版。"""
import difflib, hashlib, io, os, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

A = r'C:\Users\FisheryField\AppData\Local\Temp\TCP真实运动2.py'
B = r'D:\mydata\workspace\_rdk_scripts\TCP真实运动_2472874.py'

ta = io.open(A, encoding='utf-8', errors='replace').read()
tb = io.open(B, encoding='utf-8', errors='replace').read()

for tag, t, p in (('TEMP\\TCP真实运动2.py（实际运行）', ta, A), ('站内活动版', tb, B)):
    print('\n===== %s =====' % tag)
    print('  行数=%d 字符=%d sha256=%s' % (t.count('\n') + 1, len(t), hashlib.sha256(t.encode('utf-8')).hexdigest()[:16]))
    for pat in ['_real_running', 'real_deviation_var', 'spin360', '_retreat_orientation_records',
                'require_linear', '磨砂圆柱', '_plan_cache', 'ROBOT_SPEED']:
        m = re.findall(pat + r'[^\n]{0,40}', t)
        print('  %-28s %d 处  %s' % (pat, t.count(pat), (m[0][:60] if m else '')))
    print('  模块级 _real_running 定义: %s' % bool(re.search(r'^_real_running\s*=', t, re.M)))

print('\n===== 差异块数 =====')
d = list(difflib.unified_diff(tb.splitlines(), ta.splitlines(), 'station', 'TEMP_run', lineterm='', n=0))
print('@@ 块数 =', sum(1 for l in d if l.startswith('@@')))
print('\n前 80 行差异：')
for l in d[:80]:
    print(l[:170])
