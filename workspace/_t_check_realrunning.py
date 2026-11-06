# -*- coding: utf-8 -*-
"""核查 _real_running 的模块级初始化在各副本中的有无（潜在 NameError）。"""
import io, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
d = open(r'D:\mydata\workspace\_rdk_unpacked.bin', 'rb').read()
starts = [381, 663, 1861146, 1861423, 1910353, 1910630, 1959341, 1959618,
          2010152, 2010176, 2013647, 2049439, 2050611, 2125317, 2125607,
          2178937, 2179227, 2233499, 2233776, 2290336, 2290613, 2355543,
          2355833, 2410137, 2410523, 2472874, 2473317]

def block(o):
    z = d.find(b'\x00', o)
    return d[o:z if z > 0 else len(d)].decode('utf-8', 'replace')

def modlevel_def(t):
    """是否存在模块级（行首无缩进、非函数内） _real_running = ..."""
    return bool(re.search(r'^_real_running\s*=', t, re.M))

def global_decl(t):
    return bool(re.search(r'^\s+global _real_running', t, re.M))

print('%-10s %-9s %-12s %-9s %s' % ('offset', '定义?', 'global声明?', '行数', '首行docstring片段'))
for o in starts:
    t = block(o)
    if not t.startswith('#'):
        continue
    first_doc = ''
    m = re.search(r'"""\n(.*?)\n', t, re.S)
    if m:
        first_doc = m.group(1)[:60]
    print('%-10d %-9s %-12s %-9d %s' % (o, modlevel_def(t), global_decl(t), t.count('\n')+1, first_doc))

print('\n=== 磁盘两版 ===')
for p in (r'D:\mydata\workspace\机械臂TCP真实运动.py',
          r'D:\mydata\working things\dobot_arm\RoboDK files 2\机械臂TCP真实运动.py'):
    t = io.open(p, encoding='utf-8', errors='replace').read()
    print('%-70s 定义=%s  global=%s  行数=%d' % (p[-60:], modlevel_def(t), global_decl(t), t.count('\n')+1))

print('\n=== 活动版相关片段 ===')
t = block(2472874)
lines = t.splitlines()
for i, l in enumerate(lines, 1):
    if '_real_running' in l:
        print('%5d | %s' % (i, l))
print('\n--- 518-530 行 ---')
for i in range(517, 531):
    print('%5d | %s' % (i+1, lines[i]))
