# -*- coding: utf-8 -*-
"""证据：今天工作站每次存盘的时间 vs 脚本运行时刻 → 证明驱动当时是否在正常工作。"""
import hashlib, os, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

D = r'D:\mydata\working things\dobot_arm\RoboDK files 2'
for name in ('2026-9-7.rdk', '2026-9-26.rdk'):
    p = os.path.join(D, name)
    if not os.path.exists(p):
        continue
    st = os.stat(p)
    h = hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
    print('%-16s 大小=%-8d 修改=%s  sha=%s' % (
        name, st.st_size, time.strftime('%m-%d %H:%M:%S', time.localtime(st.st_mtime)), h))

print('\n=== 今天(10-09) sim_scripts 与 TEMP 里被脚本/驱动写过的文件 ===')
for d in (r'D:\mydata\glm-workplace\sim_scripts',
          os.environ.get('TEMP', '')):
    if not d or not os.path.isdir(d):
        continue
    for f in sorted(os.listdir(d)):
        fp = os.path.join(d, f)
        if not os.path.isfile(fp):
            continue
        st = os.stat(fp)
        if time.strftime('%m-%d', time.localtime(st.st_mtime)) == '10-09':
            print('  %s %9d  %s' % (time.strftime('%H:%M:%S', time.localtime(st.st_mtime)), st.st_size, fp))
