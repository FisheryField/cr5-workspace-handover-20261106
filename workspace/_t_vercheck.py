# -*- coding: utf-8 -*-
"""核对：站内活动脚本是否 == v10 运行副本；以及 _move_with_completion_check 的版本关系。"""
import hashlib, io, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

paths = {
    '站内活动脚本(未跑过)': r'D:\mydata\workspace\_rdk_scripts\TCP真实运动_2472874.py',
    '运行副本 %TEMP%\\TCP真实运动2.py (v10)': r'C:\Users\FisheryField\AppData\Local\Temp\TCP真实运动2.py',
    'sim_scripts\\TCP真实运动_升级版.py': r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_升级版.py',
    'sim_scripts\\TCP真实运动_当前.py': r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_当前.py',
    'RoboDK目录\\机械臂TCP真实运动.py (9/26)': r'D:\mydata\working things\dobot_arm\RoboDK files 2\机械臂TCP真实运动.py',
}
data = {}
for tag, p in paths.items():
    try:
        t = io.open(p, encoding='utf-8', errors='replace').read()
    except OSError as e:
        print('%-45s 打不开 %s' % (tag, e)); continue
    data[tag] = t
    ver = re.search(r"LOG_VERSION\s*=\s*'([^']+)'", t)
    print('%-45s 行=%-5d 字节=%-7d v10特征(分瓣/settle/静置等待)=%s%s' % (
        tag, t.count('\n') + 1, len(t.encode('utf-8')),
        ('分瓣' in t) and ('_single_move_settle' in t) and ('_wait_controller_static' in t),
        ('  LOG_VERSION=' + ver.group(1)) if ver else ''))

# v10 的偏移修正指纹
print('\n--- 30004 偏移指纹 ---')
for tag, t in data.items():
    m = re.findall(r"unpack_from\('<6d', packet,\s*(\d+)\)", t)
    print('%-45s 关节偏移=%s' % (tag, m))

# _real_running 模块级定义
print('\n--- _real_running 模块级初始化 ---')
for tag, t in data.items():
    print('%-45s %s' % (tag, bool(re.search(r'^_real_running\s*=\s*False', t, re.M))))

# 站内版与运行副本的具体差异块（只看执行链）
A = data.get('运行副本 %TEMP%\\TCP真实运动2.py (v10)')
B = data.get('站内活动脚本(未跑过)')
if A and B:
    import difflib
    d = list(difflib.unified_diff(B.splitlines(), A.splitlines(), 'station', 'v10', lineterm='', n=0))
    print('\n站内版 → v10 差异块数 =', sum(1 for l in d if l.startswith('@@')))
